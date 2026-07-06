# Mengungkap "Silent Bug" di dbt BigQuery: Dynamic vs Static Partitioning pada Strategi `insert_overwrite`

Apakah Anda menggunakan dbt (data build tool) dengan Google BigQuery? Jika ya, kemungkinan besar Anda sudah familiar dengan **Incremental Models**. Salah satu strategi incremental paling populer di BigQuery adalah **`insert_overwrite`**. Strategi ini sangat efisien karena alih-alih memindai seluruh tabel atau melakukan merge baris-demi-baris (yang memakan biaya besar di BigQuery), dbt akan menimpa (*overwrite*) partisi target secara utuh berdasarkan data baru yang masuk.

Namun, tahukah Anda bahwa ada perbedaan perilaku krusial antara **Dynamic Partitioning** (default) dan **Static Partitioning**? Jika salah konfigurasi, Anda bisa mengalami masalah kualitas data yang serius: data lama yang seharusnya terhapus dari partisi target ternyata **tetap tersimpan** di sana. Masalah ini biasa disebut sebagai *silent data issue* karena perintah `dbt run` akan sukses tanpa memunculkan error sama sekali!

Di artikel ini, kita akan membongkar perbedaan mendalam di antara keduanya melalui skenario eksperimen langsung beserta analisis query SQL di balik layar.

---

## 1. Konsep Dasar: Dynamic vs Static Partitioning di dbt-BigQuery

Pada dbt-BigQuery, strategi `insert_overwrite` memiliki dua mode untuk menentukan partisi mana saja di tabel tujuan yang akan ditimpa:

1. **Dynamic Partitioning (Tanpa parameter `partitions` di config)**:
   dbt memindai data hasil query model Anda terlebih dahulu, mencari nilai partisi yang unik (misalnya tanggal order), lalu menimpa partisi-partisi target tersebut.
2. **Static Partitioning (Dengan parameter `partitions` di config)**:
   Anda secara eksplisit mendefinisikan daftar partisi yang ingin ditimpa dalam konfigurasi model (misalnya menggunakan *variable* atau fungsi tanggal). dbt akan langsung menimpa partisi target tersebut tanpa mempedulikan apakah hasil query model untuk partisi tersebut berisi baris data atau kosong.

---

## 2. Eksperimen: Mereproduksi Masalah

Mari kita lakukan simulasi sederhana menggunakan data transaksi pesanan untuk melihat bagaimana masalah ini terjadi.

### Langkah 1: Persiapan Data Staging
Pertama, buat tabel staging untuk mensimulasikan data transaksi masuk:

```sql
CREATE OR REPLACE TABLE dev.stg_orders (
    order_id INT64,
    order_date DATE,
    updated_at TIMESTAMP,
    amount NUMERIC
);
```

Kita masukkan data transaksi untuk 3 hari terakhir (H-3 hingga H-1) menggunakan script data generator [generate_orders.py](file:///home/al/Projects/sandbox-hub/analysis/dbt-bq/generate_orders.py):
```sql
TRUNCATE TABLE dev.stg_orders;
INSERT INTO dev.stg_orders VALUES
(1, DATE '2026-07-03', TIMESTAMP '2026-07-06 20:12:00', 101),
(2, DATE '2026-07-03', TIMESTAMP '2026-07-06 20:12:00', 102),
(3, DATE '2026-07-03', TIMESTAMP '2026-07-06 20:12:00', 103),
(4, DATE '2026-07-04', TIMESTAMP '2026-07-06 20:12:00', 104),
(5, DATE '2026-07-04', TIMESTAMP '2026-07-06 20:12:00', 105),
(6, DATE '2026-07-04', TIMESTAMP '2026-07-06 20:12:00', 106),
(7, DATE '2026-07-05', TIMESTAMP '2026-07-06 20:12:00', 107),
(8, DATE '2026-07-05', TIMESTAMP '2026-07-06 20:12:00', 108),
(9, DATE '2026-07-05', TIMESTAMP '2026-07-06 20:12:00', 109);
```

### Langkah 2: Membuat Model dbt Awal (Dynamic Partitioning)
Kita buat model dbt bernama [fact_orders_static.sql](file:///home/al/Projects/sandbox-hub/analysis/dbt-bq/sans/models/fact_orders_static.sql). Sebagai langkah awal pengujian **Dynamic Partitioning**, mari kita bayangkan model dbt yang *tidak* menggunakan parameter `partitions` pada config block-nya:

```sql
{{ config(
    materialized='incremental',
    incremental_strategy='insert_overwrite',
    partition_by={
      "field": "order_date",
      "data_type": "date",
      "granularity": "day"
    }
) }}

SELECT 
    *
from {{ source('dev', 'stg_orders') }}

{% if is_incremental() %}
-- Memproses data H-1 untuk efisiensi run incremental
WHERE order_date = date_sub(current_date(), interval 1 day)
{% endif %}
```

Jalankan perintah dbt pertama kali secara full-refresh untuk menginisialisasi tabel target:
```bash
dbt run --select fact_orders_static --full-refresh
```
Seluruh data dari H-3 hingga H-1 berhasil masuk ke tabel `fact_orders_static`.

### Langkah 3: Menghapus Data di Staging (Titik Masalah)
Bagaimana jika terjadi koreksi data di mana transaksi pada H-1 (misalnya tanggal `2026-07-05`) **dihapus sepenuhnya** dari staging?

```sql
DELETE FROM dev.stg_orders
WHERE order_date = date_sub(current_date(), interval 1 day);
```
Sekarang, tabel staging `dev.stg_orders` tidak memiliki data sama sekali untuk tanggal `2026-07-05`.

---

## 3. Analisis Hasil Incremental Run

### Skenario A: Menggunakan Dynamic Partitioning
Mari kita jalankan dbt run secara incremental:
```bash
dbt run --select fact_orders_static
```
* **Hasil yang Diharapkan**: Partisi `2026-07-05` di tabel target ikut kosong (terhapus), menyelaraskan diri dengan staging.
* **Hasil Aktual**: Data tanggal `2026-07-05` **masih ada** di tabel target! `dbt run` selesai dengan sukses, namun data usang (*stale*) tidak terhapus.

#### Mengapa Dynamic Partitioning Gagal? (Bedah SQL)
Jika kita melihat SQL yang dihasilkan pada dbt target run (lihat [incr_insow_dynamic_partitions.sql](file:///home/al/Projects/sandbox-hub/analysis/dbt-bq/incr_insow_dynamic_partitions.sql)), dbt melakukan langkah berikut:

1. **Membuat tabel temporary** untuk menampung hasil query model:
   ```sql
   create or replace table `dev`.`fact_orders_static__dbt_tmp` as (
     SELECT * from `dev`.`stg_orders`
     WHERE order_date = date_sub(current_date(), interval 1 day)
   );
   ```
   *Karena data H-1 di staging sudah kosong, tabel temporary ini memiliki **0 baris data**.*

2. **Mendeteksi daftar partisi** secara dinamis dari tabel temporary:
   ```sql
   declare dbt_partitions_for_replacement array<date>;
   set (dbt_partitions_for_replacement) = (
       select as struct
           array_agg(distinct date(order_date) IGNORE NULLS)
       from `dev`.`fact_orders_static__dbt_tmp`
   );
   ```
   *Karena tabel temporary kosong, variabel `dbt_partitions_for_replacement` bernilai **empty array (`[]`)** atau **`NULL`**.*

3. **Melakukan MERGE statement** untuk menimpa target:
   ```sql
   merge into `dev`.`fact_orders_static` as DBT_INTERNAL_DEST
   using (
       select * from `dev`.`fact_orders_static__dbt_tmp`
   ) as DBT_INTERNAL_SOURCE
   on FALSE
   when not matched by source
        and date(DBT_INTERNAL_DEST.order_date) in unnest(dbt_partitions_for_replacement) 
       then delete
   when not matched then insert ...
   ```
   Perhatikan bagian:
   `and date(DBT_INTERNAL_DEST.order_date) in unnest(dbt_partitions_for_replacement)`
   
   Karena variabel `dbt_partitions_for_replacement` bernilai kosong, kondisi `in unnest(...)` bernilai salah (`false`) untuk semua baris. Akibatnya, BigQuery tidak menghapus partisi target apa pun. Data lama di partisi `2026-07-05` tetap aman bersemayam di tabel target.

---

### Skenario B: Menggunakan Static Partitioning
Sekarang, mari kita konfigurasi model dbt kita agar menggunakan Static Partitioning dengan menambahkan parameter `partitions` pada config block seperti pada file [fact_orders_static.sql](file:///home/al/Projects/sandbox-hub/analysis/dbt-bq/sans/models/fact_orders_static.sql):

```sql
{{ config(
    materialized='incremental',
    incremental_strategy='insert_overwrite',
    partition_by={
      "field": "order_date",
      "data_type": "date",
      "granularity": "day"
    },
    partitions=[var('start_date')] -- Menentukan partisi target secara statis
) }}

SELECT 
    *
from {{ source('dev', 'stg_orders') }}

{% if is_incremental() %}
WHERE order_date = {{ var("start_date") }}
{% endif %}
```

Mari kita jalankan dbt run dengan menyuplai tanggal target melalui variable:
```bash
dbt run --select fact_orders_static --vars '{"start_date": "date_sub(current_date(), interval 1 day)"}'
```
* **Hasil Aktual**: Data tanggal `2026-07-05` di tabel target **berhasil terhapus** (menjadi kosong), sesuai dengan kondisi staging terbaru!

#### Mengapa Static Partitioning Berhasil? (Bedah SQL)
Mari kita lihat SQL hasil compile untuk Static Partitioning (lihat [incr_insow_static_partitions.sql](file:///home/al/Projects/sandbox-hub/analysis/dbt-bq/incr_insow_static_partitions.sql)):

```sql
merge into `dev`.`fact_orders_static` as DBT_INTERNAL_DEST
using (
    SELECT * from `dev`.`stg_orders`
    WHERE order_date = date_sub(current_date(), interval 1 day)
) as DBT_INTERNAL_SOURCE
on FALSE
when not matched by source
     and date(DBT_INTERNAL_DEST.order_date) in (
            date_sub(current_date(), interval 1 day)
        ) 
    then delete
when not matched then insert ...
```
Perhatikan perbedaannya:
- dbt tidak membuat tabel temporary atau mendeklarasikan variabel array partisi dinamis.
- Daftar partisi langsung di-hardcode ke dalam query `merge` di bagian `when not matched by source and date(DBT_INTERNAL_DEST.order_date) in (...)`.
- Meskipun subquery `using (...)` dari staging menghasilkan 0 baris, kondisi `date(DBT_INTERNAL_DEST.order_date) in (date_sub(current_date(), interval 1 day))` tetap dievaluasi untuk setiap baris di tabel tujuan.
- Karena baris H-1 di tabel tujuan tidak memiliki pasangan di source (karena source kosong), kondisi `when not matched by source` terpenuhi, dan baris-baris tersebut **berhasil dihapus**.

---

## 4. Perbandingan & Rekomendasi Utama

| Fitur / Perilaku | Dynamic Partitioning | Static Partitioning |
| :--- | :--- | :--- |
| **Konfigurasi** | Cukup `partition_by` saja | Butuh `partition_by` + `partitions` |
| **Pembuatan Temp Table** | Ya, untuk mendeteksi partisi | Tidak wajib (dbt langsung merge) |
| **Kasus Source Partisi Kosong** | ⚠️ **Silent Bug**: Data target lama tetap tersimpan | ✅ **Aman**: Data target lama dihapus |
| **Scan Cost (BigQuery)** | Lebih hemat jika partisi dinamis bervariasi | Terkontrol penuh sesuai definisi partisi |

### Rekomendasi Best Practice:
1. **Gunakan Static Partitioning untuk Daily Batch Ingestion**: Jika pipeline dbt Anda memproses rentang tanggal yang terdefinisi dengan jelas setiap harinya (misal: H-1 saja), **selalu gunakan Static Partitioning**. Ini menghindarkan Anda dari risiko data stale ketika data source kosong.
2. **Manfaatkan Variabel dbt untuk Fleksibilitas**: Gunakan parameter `var` di dbt agar rentang tanggal partisi dapat diubah secara dinamis saat dijalankan secara manual (misalnya untuk proses *backfill* data lama).
   ```sql
   partitions=[var('start_date')]
   ```
3. **Waspada Jika Menggunakan Dynamic Partitioning**: Jika terpaksa menggunakan dynamic partition (misalnya karena data staging mencakup tanggal yang acak dan banyak), pastikan Anda memasang data kualitas pengujian (dbt data tests) untuk memverifikasi keselarasan row count antara staging dan target model.