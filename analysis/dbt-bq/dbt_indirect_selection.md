# Mengapa `dbt test -s dim_customers` Gagal dengan Error `Table fct_orders Not Found`?

Pernahkah Anda hanya ingin menguji satu tabel dimensi di lokal atau CI (`dbt test -s dim_customers`), tetapi dbt justru **CRASH** dengan error seperti ini?

```text
1 of 3 START test check_orders_customer_fk_to_dim_customers... [RUN]
1 of 3 ERROR check_orders_customer_fk_to_dim_customers...
  Database Error: Not found: Table dev.fct_orders was not found in location US
```

Padahal Anda **tidak pernah** mendefinisikan test tersebut di `dim_customers.yml`! Test tersebut ditulis di file `fct_orders.yml` milik model fakta.

Di artikel ini, kita akan membongkar:
1. **Mengapa test dari file `.yml` lain ikut terseret saat me-run `dbt test -s dim_customers`?**
2. **Mitos: Apakah test tersebut berjalan 2x jika kita me-select kedua model?**
3. **Solusi cepat & permanen menggunakan `--indirect-selection cautious`.**

---

## 1. Kronologi Masalah: "Beda File `.yml`, Tapi Tetap Terseret"

Bayangkan struktur project dbt Anda:
```text
models/
├── dim_customers.sql
├── dim_customers.yml
├── fct_orders.sql
└── fct_orders.yml
```

Di dalam `fct_orders.yml`, Anda mendefinisikan kustom nama test `check_orders_customer_fk_to_dim_customers` untuk memverifikasi `customer_id` di `dim_customers`:

```yaml
# fct_orders.yml
version: 2

models:
  - name: fct_orders
    tests:
      - row_count_equal:
          name: check_orders_row_count_matches_customers
          arguments:
            compare_model: ref('dim_customers')
    columns:
      - name: customer_id
        tests:
          - relationships:
              name: check_orders_customer_fk_to_dim_customers
              arguments:
                to: ref('dim_customers')
                field: customer_id
```

### Skenario Eksekusi:
Anda hanya mengubah dan membangun tabel `dim_customers`:
```bash
dbt run -s dim_customers
dbt test -s dim_customers
```

### Hasil Log Terminal:
```text
Found 4 models, 3 data tests
1 of 3 START test check_orders_customer_fk_to_dim_customers... [RUN]
1 of 3 ERROR check_orders_customer_fk_to_dim_customers... 
  Database Error: Not found: Table dev.fct_orders was not found
```

### 🔍 Mengapa Test dari `fct_orders.yml` Ikut Dijalankan?
Secara default, dbt menggunakan mode **`--indirect-selection eager`**.

Di mode `eager`, dbt membaca bahwa test `check_orders_customer_fk_to_dim_customers` di file `fct_orders.yml` menyebutkan `ref('dim_customers')`. dbt mengevaluasi:
> *"Test ini menyentuh `dim_customers`. Karena Anda menjalankan `--select dim_customers`, maka test dari `fct_orders.yml` ini WAJIB diikutsertakan."*

Karena Anda **baru me-run `dim_customers`** dan **belum me-run `fct_orders`**, tabel `fct_orders` belum ada di database. Test pun **CRASH / FAIL** karena tidak menemukan tabel `fct_orders`!

---

## 2. Mitos: "Apakah Test Tersebut Berjalan 2x Jika Kedua Model Di-select?"

Banyak data engineer khawatir: Jika kita menjalankan `dbt test -s fct_orders dim_customers`, apakah test `check_orders_customer_fk_to_dim_customers` tersebut akan dipanggil **2 kali** (sekali oleh `fct_orders` dan sekali oleh `dim_customers`)?

**Jawabannya: TIDAK.**

dbt memiliki mekanisme **Node De-duplication** dalam 1 kali eksekusi (*invocation*):
- dbt menyusun DAG dan mendaftarkan **Unique Node ID** untuk setiap test (contoh: `sans.indirect_selection.check_orders_customer_fk_to_dim_customers`).
- Walaupun test tersebut di-indirect oleh `fct_orders` DAN `dim_customers`, dbt melihat Node ID tersebut sama.
- dbt menjamin test tersebut hanya dieksekusi **tepat 1x saja** dalam satu perintah `dbt test`.

---

## 3. Solusi Cerdas: Mode `--indirect-selection cautious`

Untuk mencegah test dari `fct_orders.yml` terseret saat Anda hanya menguji `dim_customers`, gunakan flag **`cautious`**:

```bash
dbt test -s dim_customers --indirect-selection cautious
```

### Perilaku Mode `cautious`:
dbt mengevaluasi:
> *"Test `check_orders_customer_fk_to_dim_customers` ini membutuhkan DUA tabel: `fct_orders` dan `dim_customers`. Karena Anda hanya memilih `dim_customers`, test ini gue **SKIP**."*

### Hasil Eksekusi:
Test tersebut otomatis di-skip, dan `dbt test` selesai dengan status **PASS (0 Error)** tanpa perlu memanggil tabel `fct_orders` yang belum dibuat!

---

## 4. Konfigurasi Permanen untuk CI/CD & Local

Daripada mengetik flag CLI terus-menerus, Anda bisa memasangnya secara permanen:

### A. Di `dbt_project.yml`:
```yaml
flags:
  indirect_selection: cautious
```

### B. Di Pipeline CI/CD (GitHub Actions / GitLab CI):
```bash
export DBT_INDIRECT_SELECTION=cautious
```

---

## 5. Ringkasan

| Pertanyaan | Mode `eager` (Default) | Mode `cautious` (Rekomendasi) |
| :--- | :--- | :--- |
| **`dbt test -s dim_customers`** (Test tertulis di `fct_orders.yml`) | ❌ **Terseret & Error** (`fct_orders not found`) | ✅ **Di-skip** (Aman & Bebas Error) |
| **`dbt test -s fct_orders dim_customers`** | ✅ Dijalankan **tepat 1x** (Dideduplikasi) | ✅ Dijalankan **tepat 1x** (Dideduplikasi) |
