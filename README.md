# 📊 Transaction Analytics Dashboard

[![Release](https://img.shields.io/badge/release-v1.0.0-blue)](https://github.com/ilfijandrisno/Transaction-Analytics-Dashboard/releases) [![Python](https://img.shields.io/badge/python-3.13%2B-blue?logo=python)](https://www.python.org/) [![Streamlit](https://img.shields.io/badge/Streamlit-1.45.1-FF4B4B?logo=streamlit)](https://streamlit.io/) [![Plotly](https://img.shields.io/badge/Plotly-6.3.0-3F4F75?logo=plotly)](https://plotly.com/python/) ![Last Commit](https://img.shields.io/github/last-commit/ilfijandrisno/Transaction-Analytics-Dashboard)  ![Repo Size](https://img.shields.io/github/repo-size/ilfijandrisno/Transaction-Analytics-Dashboard) ![Stars](https://img.shields.io/github/stars/ilfijandrisno/Transaction-Analytics-Dashboard?style=social)

<img src="assets/0.Filter_Overview.png" alt="Dashboard Preview" width="300"> <img src="assets/2.BussinessMix.png" alt="Dashboard Preview" width="300"> <img src="assets/3.Reliability.png" alt="Dashboard Preview" width="300">


## 📌 Deskripsi
**Transaction Analytics Dashboard** adalah aplikasi interaktif berbasis **[Streamlit](https://streamlit.io/)** yang dirancang untuk memantau dan menganalisis data transaksi dari berbagai kategori produk/layanan, channel distribusi, dan wilayah pemasaran.

Dashboard ini membantu **tim bisnis, manajemen, dan operasional** untuk:
- Memantau **nilai transaksi** (Total Transaction Value)
- Melihat **Fee-Based Revenue**
- Mengukur **Success Rate** transaksi
- Menganalisis **distribusi bisnis** berdasarkan kategori, channel, dan region
- Memantau **reliabilitas dan kinerja** per periode

Dataset yang digunakan adalah **dummy data** yang disimulasikan untuk 3 tahun terakhir..

---

## 📂 Struktur Dashboard

### 1️⃣ **Weekly Dashboard**
- Menampilkan KPI mingguan
- Filter: **Year**, **Month**, **Category**, **Channel**, **Region**
- Cocok untuk memantau tren mingguan secara rinci

### 2️⃣ **Monthly Dashboard**
- Analisis kinerja bulanan
- Filter: **Year**, **Category**, **Channel**, **Region**
- Memudahkan evaluasi performa tiap bulan

### 3️⃣ **Quarterly Dashboard**
- Ringkasan per kuartal
- Filter: **Year**, **Category**, **Channel**, **Region**
- Berguna untuk review bisnis per kuartal

### 4️⃣ **Yearly Dashboard**
- Gambaran besar kinerja tahunan
- Filter: **Category**, **Channel**, **Region**
- Cocok untuk laporan akhir tahun

---

## 📊 Komponen Analisis

<p align="center">
  <img src="assets/1.Overview.png" alt="Dashboard Preview" width="100%">
</p>

### 🔹 **Overview**
Menampilkan ringkasan indikator utama (KPI) berdasarkan periode terpilih:
- **Total Transaction Value** → Nilai total seluruh transaksi.
- **Fee-Based Revenue** → Total pendapatan dari biaya transaksi.
- **Success Rate** → Persentase keberhasilan transaksi.
- **GMV / Avg GMV per Active User** → Nilai transaksi rata-rata per pengguna aktif. 

---

### 🔹 **Business Mix**

<p align="center">
  <img src="assets/2.BussinessMix.png" alt="Dashboard Preview" width="100%">
</p>

Menganalisis komposisi bisnis dari berbagai perspektif:
- **Fee by Category** → Nilai fee per kategori produk/layanan.
- **Share of Transactions by Category** → Persentase jumlah transaksi tiap kategori dibandingkan total transaksi keseluruhan (membantu mengidentifikasi kategori dominan).
- **Channel Distribution** → Distribusi transaksi berdasarkan channel (Agent, App, Web).
- **Regional Distribution** → Distribusi transaksi per wilayah (pie chart).

---

### 🔹 **Reliability & Monitoring**

<p align="center">
  <img src="assets/3.Reliability.png" alt="Dashboard Preview" width="100%">
</p>

- **Success vs Failed by Category** → Membandingkan jumlah transaksi sukses dan gagal untuk tiap kategori, dengan warna **hijau** (success) dan **merah** (failed).
- **Failure Reasons (Top)** → Menampilkan daftar alasan kegagalan transaksi terbanyak.

---

### 🔹 **Users**

<p align="center">
  <img src="assets/4.Users.png" alt="Dashboard Preview" width="100%">
</p>

- **Active Users by Channel** → Jumlah pengguna aktif dibagi berdasarkan channel distribusi.
- **Active Users by Region** → Jumlah pengguna aktif per wilayah pemasaran.

---

## 🗂 Struktur Data Dummy

| Kolom               | Deskripsi |
|---------------------|-----------|
| `date`              | Tanggal transaksi |
| `year`              | Tahun transaksi |
| `month`             | Nama bulan transaksi |
| `week`              | Nomor minggu transaksi |
| `quarter`           | Nomor kuartal (1–4) |
| `category`          | Jenis produk/layanan (Airtime, Data Bundle, dll.) |
| `channel`           | Saluran distribusi (Agent, App, Web) |
| `region`            | Wilayah pemasaran (Zone 1–6, Unmapped) |
| `transaction_value` | Nilai transaksi (dalam satuan mata uang) |
| `fee_based_revenue` | Pendapatan berbasis fee |
| `status`            | Status transaksi (Success / Failed) |

> File data default: **`data/transactions_dummy.csv`** (diletakkan di direktori data).  
> Format kolom mengikuti skema di atas.
---

## 🚀 Cara Menjalankan di Lokal

1. **Clone Repository**
   ```bash
   git clone https://github.com/ilfijandrisno/Transaction-Analytics-Dashboard.git
   cd Transaction-Analytics-Dashboard
   ```
2. **Instalasi Dependensi**
   ```python
   pip install -r requirements.txt
   ```
3. **Jalankan Aplikasi**
   ```python
   streamlit run streamlit_app.py
   ```