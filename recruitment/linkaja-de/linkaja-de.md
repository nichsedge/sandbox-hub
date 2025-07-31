# LinkAja - Data Engineer

1. Buatlah skrip Python yang dapat menghasilkan pola segitiga yang berisi angka dari barisan Golomb (https://oeis.org/A001462) dengan argumen baris sebagai input Berikan penjelasan langkah-langkah detil dan analisis algoritma dalam comment pada skrip.

![alt text](Reflections/post/2024-02-11-linux/image.png)

Skrip dapat ditemukan di `golomb_pyramid.py`. Langkah paling efisien dapat dilakukan dengan dynamic programming, berdasarkan referensi dari https://www.tutorialspoint.com/golomb-sequence dan https://www.geeksforgeeks.org/golomb-sequence-set-2/.

Pertama, perlu diketahui jumlah angka barisan Golomb yang dibutuhkan untuk membentuk piramida dengan formula dari barisan aritmatika. Selanjutnya, setelah barisan tersebut ada, kita dapat mencetak piramida.

Time complexity untuk fungsi `golomb` adalah O(n), di mana n adalah jumlah angka dalam barisan, bukan tinggi piramida dari input program. Time complexity untuk fungsi `print_pyramid` juga adalah O(n), sehingga overall time complexity-nya adalah O(n).

Space complexity adalah O(n) untuk fungsi `golomb` dan O(1) untuk fungsi `print_pyramid`, sehingga secara keseluruhan, space complexity-nya adalah O(n).


2. Gunakan data ini pada PostgreSQL, lakukan query SQL untuk menyelesaikan problem berikut:

a. Import file CSV ke sebuah table bernama movies (gunakan tool psql atau lainnya).

Ada banyak opsi untuk hal ini, biasanya saya menggunakan Pandas karena lebih simpel apabila data tidak terlalu besar.

`df.to_sql(name='movies', con=engine, schema='public', if_exists='replace', method='multi', index=False)`

Opsi lainnya adalah membuat tabel dahulu di PosgreSQL dengan DLL berikut.

```sql
CREATE TABLE public.movies (
	"Rank" int8 NULL,
	"Title" text NULL,
	"Genre" text NULL,
	"Description" text NULL,
	"Director" text NULL,
	"Actors" text NULL,
	"Year" int8 NULL,
	"Runtime (Minutes)" int8 NULL,
	"Rating" float8 NULL,
	"Votes" int8 NULL,
	"Revenue (Millions)" float8 NULL,
	"Metascore" float8 NULL
);
```

Kemudian gunakan `COPY` statement untuk populate table dari CSV. 

```sql
COPY public.movies FROM '/path/to/movies.csv' WITH DELIMITER ',' CSV HEADER;
```



b. Di table movies, cari film animasi dengan rating 6 keatas, setelah tahun 2010 dengan votes lebih dari 10 ribu. Urut berdasarkan rating tertinggi sampai terendah.

Berikut kuerinya:

```sql
SELECT 
    "Rank" AS rank,
    "Title" AS title,
    "Genre" AS genre,
    "Description" AS description,
    "Director" AS director,
    "Actors" AS actors,
    "Year" AS year,
    "Runtime (Minutes)" AS runtime_minutes,
    "Rating" AS rating,
    "Votes" AS votes,
    "Revenue (Millions)" AS revenue_millions,
    "Metascore" AS metascore
FROM 
    movies m
WHERE 
    "Genre" LIKE '%Animation%' 
    AND "Year" > 2010
    AND "Votes" > 10000
ORDER BY 
    "Rating" DESC NULLS LAST;
```

Berikut hasilnya:

![alt text](Reflections/post/2024-02-13-sql-null-values/image-1.png)


c. Buat table baru bernama actors untuk menyimpan informasi film-film apa saja yang dimainkan oleh seorang actor, dengan kolom actor_name, title, year, rating dan metascore. Urut table tersebut berdasarkan rating tertinggi sampai terendah. Gunakan CTE untuk menyelesaikan soal ini.

Menurut saya tidak perlu CTE karena kueri tidak terlalu kompleks. Berikut kuerinya.

```sql
CREATE TABLE IF NOT EXISTS actors AS 
SELECT
    TRIM(UNNEST(STRING_TO_ARRAY("Actors", ','))) AS actor_name,
    "Title" AS title,
    "Year" AS year,
    "Rating" AS rating,
    "Metascore" AS metascore
FROM 
    movies m
ORDER BY 
    "Rating" DESC NULLS LAST;
```

Berikut hasilnya:

![alt text](image-2.png)


3. Buatlah sebuah sistem data pipeline hipotetik dengan interval yang berjalan setiap hari Sabtu dan Minggu jam 01.00 pagi. Gunakan Bash/Python/atau bahasa pemrograman lain.

Saya menggunakan Apache Airflow dengan Python untuk mengelola alur kerja, dan BigQuery sebagai database OLAP. Berikut adalah deskripsi singkat untuk setiap langkah dalam pipeline:

Semua langkah dalam pipeline dijalankan menggunakan jadwal interval yang diatur pada hari Sabtu dan Minggu pukul 01.00 UTC (diasumsikan sebagai waktu UTC+0). Dengan demikian, pipeline berjalan secara teratur sesuai dengan jadwal yang ditentukan. Kode dapat dilihat pada folder `airflow`. Berikut UI dari airflow nya.

![alt text](image-6.png)

![alt text](image-7.png)

a. Mengimpor file dari CSV ke tabel PostgreSQL. (lihat 2a)

Task `delete_pg_task` digunakan untuk menghapus data dari tabel PostgreSQL agar pipeline bersifat idempoten. Kemudian, task `csv2pg_task` digunakan untuk mengimpor data dari file CSV ke tabel PostgreSQL.

b. Mengekspor data (lihat 2b) dari tabel movies di PostgreSQL ke file JSON.

Task `pg2json_task` mengambil data dari tabel movies di PostgreSQL dan mengekspornya ke dalam format file JSON. Hasil ekspor disimpan dalam file JSON.

![alt text](image-4.png)

c. Mengimpor file JSON ke database OLAP seperti BigQuery, Presto, Hive, dan sebagainya.

di sini saya membuat task `json2bq_task`. berikut hasilnya setelah data masuk ke bigquery.

Task `json2bq_task` mengambil file JSON yang telah diekspor sebelumnya dan mengimpornya ke BigQuery. Setelah proses impor selesai, data tersedia dalam BigQuery.

![alt text](image-5.png)

[[Data Engineering]]
