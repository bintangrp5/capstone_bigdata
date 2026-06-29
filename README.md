# Smart-WorkLife Big Data Scraper 🚀

Repositori ini berisi sistem otomatisasi *Web Scraping* dan *API Fetching* untuk mengumpulkan berita dan video terkini yang relevan dengan ekosistem aplikasi **Smart-WorkLife**. Data yang dikumpulkan akan digunakan untuk memberikan *insight* dan informasi yang produktif bagi pengguna.

## 📌 Fitur Utama

Sistem ini terdiri dari dua program utama yang berjalan secara independen menggunakan **GitHub Actions**:

1. **Scraper Detik.com (`scraper_detik.py`)**
   - **Metode**: Web Scraping asinkron menggunakan `aiohttp` dan `BeautifulSoup`.
   - **Tujuan**: Mengumpulkan berita-berita artikel terbaru berdasarkan 15 kata kunci.
   - **Jadwal Eksekusi**: Berjalan otomatis **Setiap 1 Jam** (`0 * * * *`).
   - **Sistem Anti-Duplikat**: Hanya memasukkan berita yang link-nya belum ada di database.

2. **Scraper YouTube (`scraper_youtube.py`)**
   - **Metode**: API Fetching menggunakan **YouTube Data API v3**.
   - **Tujuan**: Mengumpulkan video edukatif/informatif terbaru. Tersaring otomatis untuk menolak video pendek (Shorts) dan memastikan asal negara (Indonesia).
   - **Jadwal Eksekusi**: Berjalan otomatis **1 Kali Sehari** pada pukul 00:00 UTC / 07:00 WIB (`0 0 * * *`) untuk menghemat kuota *Search Queries* API.

## 🛠️ Teknologi yang Digunakan

- **Bahasa**: Python 3.10
- **Database**: MongoDB Atlas
- **Otomatisasi**: GitHub Actions (CI/CD)
- **Library Utama**:
  - `pandas` (Manipulasi data)
  - `beautifulsoup4` & `aiohttp` (Scraping Detik)
  - `google-api-python-client` (YouTube Data API)
  - `pymongo` (Koneksi Database)

## 🔐 Kebutuhan Environment Variables (Secrets)

Untuk menjalankan *script* ini, baik secara lokal melalui `.env` maupun melalui **GitHub Secrets**, Anda wajib menambahkan kunci-kunci berikut:

```env
MONGO_USER=username_database_anda
MONGO_PASS=password_database_anda
MONGO_CLUSTER=cluster_url_anda
MONGO_DB=Capstone
MONGO_COLLECTION=Data_Detik
MONGO_COLLECTION_YT=Data_Youtube_2
YOUTUBE_API_KEY=kunci_api_youtube_anda
```

## 🚀 Cara Menjalankan Secara Lokal

Jika Anda ingin menguji kode di komputer Anda sendiri:

1. Pastikan Anda memiliki Python 3.10+ terinstal.
2. Clone repositori ini.
3. Buat file `.env` di folder utama dan isi dengan konfigurasi di atas.
4. Install semua dependensi:
   ```bash
   pip install -r requirements.txt
   ```
5. Jalankan scraper yang diinginkan:
   ```bash
   python scraper_detik.py
   # atau
   python scraper_youtube.py
   ```

## ⏱️ Zona Waktu
Seluruh data yang masuk ke dalam sistem akan secara otomatis dikonversi dan disimpan menggunakan Cap Waktu (Timestamp) **WIB (UTC+7)**, terlepas dari lokasi server GitHub Actions yang mengeksekusinya.

---
*Dibuat untuk keperluan Capstone Project Semester 6.*
