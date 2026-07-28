# Mengapa `dbt test -s dim_customers` Error, Tapi `dbt test -s fct_orders` Menghasilkan "Nothing to do"?

Pernahkah Anda mengalami dua keanehan ini saat menggunakan `dbt test`?

### Keanehan 1 (Default Mode: `eager`)
Anda hanya menguji satu tabel dimensi (`dbt test -s dim_customers`), tetapi dbt justru **CRASH** dengan error seperti ini:
```text
1 of 3 START test check_orders_customer_fk_to_dim_customers... [RUN]
1 of 3 ERROR check_orders_customer_fk_to_dim_customers...
  Database Error: Not found: Table dev.fct_orders was not found in location US
```
Padahal Anda **tidak pernah** mendefinisikan test tersebut di `dim_customers.yml`! Test tersebut ditulis di file `fct_orders.yml` milik model fakta.

---

### Keanehan 2 (Mode: `cautious`)
Anda berpindah ke `fct_orders` dan mencoba menjalankan perintah dengan flag `cautious`:
```bash
dbt test -s fct_orders --indirect-selection cautious
```
dbt justru mengeluarkan pesan mengejutkan:
```text
Nothing to do. Try checking your model configs and model specification args
```
Padahal di file `fct_orders.yml` jelas-jelas Anda sudah mendaftarkan test `relationships` dan `row_count_equal`!

Di artikel ini, kita akan mengupas tuntas **logika di balik perilaku `dbt test`**, mengapa `Nothing to do` bisa terjadi, serta **solusi rahasia CLI dbt (`path:`) untuk skenario beda jadwal pipeline**.

---

## 1. Mengapa `dbt test -s dim_customers` Menyebabkan Error pada Mode `eager`?

Secara default, dbt menggunakan mode **`--indirect-selection eager`**.

Di mode `eager`, dbt membaca bahwa test `check_orders_customer_fk_to_dim_customers` di file `fct_orders.yml` menyebutkan `ref('dim_customers')`. dbt mengevaluasi:
> *"Test ini menyentuh `dim_customers`. Karena Anda memilih `--select dim_customers`, maka test dari `fct_orders.yml` ini WAJIB diikutsertakan."*

Karena Anda **baru me-run `dim_customers`** dan **belum me-run `fct_orders`**, tabel `fct_orders` belum ada di database. Test pun **CRASH / FAIL** karena tidak menemukan tabel `fct_orders`!

---

## 2. Mengapa `dbt test -s fct_orders --indirect-selection cautious` Menghasilkan "Nothing to do"?

Saat Anda beralih ke mode `--indirect-selection cautious` dan me-run:
```bash
dbt test -s fct_orders --indirect-selection cautious
```

Aturan mode `cautious` menyatakan:
> *"Sebuah multi-model test HANYA akan dijalankan jika **SEMUA** tabel yang di-ref() oleh test tersebut diikutsertakan dalam perintah `--select`."*

Mari kita bedah test di `fct_orders.yml`:
1. `check_orders_customer_fk_to_dim_customers` ➔ Me-`ref('fct_orders')` AND `ref('dim_customers')`.
2. `check_orders_row_count_matches_customers` ➔ Me-`ref('fct_orders')` AND `ref('dim_customers')`.

Karena Anda **hanya me-select `fct_orders`** (tanpa `dim_customers`), mode `cautious` secara tegas **MELEWATI (SKIP)** kedua test tersebut demi keamanan agar tidak terjadi error *Table not found*. 

Karena `fct_orders` tidak memiliki single-model test lain, dbt melaporkan: **`Nothing to do.`**!

---

## 3. Studi Kasus Production: Dua Model Beda Jadwal Pipeline

### 🏭 Skenario Nyata di Pipeline Produksi:
- **Jadwal 1 (Jam 01:00 AM)**: Me-run dan me-test **Tabel A (`dim_customers`)**.
- **Jadwal 2 (Jam 02:00 AM)**: Me-run dan me-test **Tabel B (`fct_orders`)**.
- Test perbandingan (misal `relationships`) ditulis di file **`fct_orders.yml`** karena Tabel B dibuat belakangan.

### ⚠️ Dilema Eksekusi:
1. **Jika Menggunakan Mode Default (`eager`)**:
   Saat Jam 01:00 AM (`dbt test -s dim_customers`), test dari `fct_orders.yml` ikut terseret dan **CRASH / ERROR** karena Tabel B belum dibangun.
2. **Jika Menggunakan Mode `cautious` Secara Naif**:
   Saat Jam 02:00 AM (`dbt test -s fct_orders --indirect-selection cautious`), test dari `fct_orders.yml` malah di-**SKIP** (`Nothing to do`) karena Tabel A tidak disebutkan dalam `-s fct_orders`!

---

### 💡 Solusi Terbaik: Trik Selector `path:` untuk Pipeline Production

Solusi paling elegan adalah mengombinasikan `--indirect-selection cautious` di Jam 01:00 AM dengan **Selector `path:`** di Jam 02:00 AM.

#### ⏰ Jam 01:00 AM (Jadwal 1 - `dim_customers`):
```bash
dbt run --select dim_customers
dbt test --select dim_customers --indirect-selection cautious
```
* **Hasil:** Test dari `fct_orders.yml` **OTOMATIS DI-SKIP** oleh mode `cautious`. Pipeline Jam 01:00 AM aman 100% dari error `Table fct_orders not found`!

#### ⏰ Jam 02:00 AM (Jadwal 2 - `fct_orders`):
```bash
dbt run --select fct_orders
dbt test --select path:models/indirect_selection/fct_orders.yml
```
* **Hasil:** Dengan menunjuk langsung file `path:fct_orders.yml`, dbt mengeksekusi seluruh test di dalam file `.yml` tersebut secara langsung tanpa terhalang filter `cautious`! Karena `dim_customers` sudah di-build pada Jam 01:00 AM, seluruh test perbandingan berjalan **100% PASS**!

---

## 4. Mitos: "Apakah Test Tersebut Berjalan 2x Jika Kedua Model Di-select?"

Jika kita me-select kedua model dalam satu perintah (`dbt test -s fct_orders dim_customers`), apakah test `relationships` akan dipanggil **2 kali**?

**Jawabannya: TIDAK.**

dbt memiliki mekanisme **Node De-duplication** dalam 1 kali eksekusi (*invocation*):
- dbt menyusun DAG dan mendaftarkan **Unique Node ID** untuk setiap test (contoh: `sans.indirect_selection.check_orders_customer_fk_to_dim_customers`).
- dbt menjamin setiap test node hanya dieksekusi **tepat 1x saja** dalam satu perintah CLI.

---

## 5. Ringkasan Sintaks & Solusi Pipeline

| Skenario Pipeline | Perintah CLI | Perilaku & Hasil |
| :--- | :--- | :--- |
| **Jadwal 1 (Jam 01:00 AM)** | `dbt test -s dim_customers --indirect-selection cautious` | ✅ **Aman (Skipped)** (Mencegah error `fct_orders not found`) |
| **Jadwal 2 (Naif)** | `dbt test -s fct_orders --indirect-selection cautious` | ⚠️ **Nothing to do** (Skipped karena `dim_customers` tidak di-select) |
| **Jadwal 2 (Trik Path `path:`)** | `dbt test -s path:fct_orders.yml` | ✅ **Lancar & Aman** (Memanggil seluruh test di `fct_orders.yml` secara langsung) |
| **Pilihan Lain (Dua Model)** | `dbt test -s fct_orders dim_customers --indirect-selection cautious` | ✅ **Lancar & Aman** (Memanggil test 1x karena kedua tabel di-select) |
