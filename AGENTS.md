# AGENTS.md - Panduan & Memori Pengembang SAVETRACK

Dokumen ini berisi standar arsitektur, konvensi penamaan, dan aturan pengembangan untuk proyek **SAVETRACK**. Semua agen dan pengembang wajib mematuhi panduan ini.

---

## 1. Ikhtisar Proyek
- **Nama Proyek:** SAVETRACK (Aplikasi Manajemen Keuangan & Multi-Rekening Mahasiswa/Personal)
- **Tujuan:** Aplikasi web pelacak keuangan fleksibel, ramah perangkat bergerak (mobile-first), siap portofolio GitHub.
- **Teknologi Utama:**
  - **Backend:** Python (FastAPI)
  - **Database:** SQLite (`backend/database/app.db`)
  - **Frontend:** HTML5, Jinja2 Templates, Tailwind CSS (via CDN), Alpine.js (via CDN)
  - **Prinsip:** Nol dependensi Node.js/bundler pada server runtime, ringan, dan cepat.

---

## 2. Standar Konvensi Penamaan (Bahasa Indonesia)

Sesuai instruksi proyek, seluruh modul, class, fungsi, file, dan folder wajib menggunakan **Bahasa Indonesia** dengan aturan penulisan:

| Elemen | Format Penulisan | Contoh |
| :--- | :--- | :--- |
| **Folder / Direktori** | `PascalCase` | `BasisData/`, `KelolaAkun/`, `AlokasiDana/`, `Transaksi/` |
| **Class** | `PascalCase` | `class SimpanUang:`, `class AkunKeuangan:`, `class AlokasiOtomatis:` |
| **File Python** | `camelCase.py` | `basisData.py`, `kelolaAkun.py`, `alokasiDana.py`, `transaksi.py` |
| **Fungsi / Metode** | `camelCase()` | `simpanUang()`, `tambahAkun()`, `hitungSisaHari()`, `ambilDaftarAkun()` |
| **Variabel** | `camelCase` / `snake_case` | `saldoAwal`, `idAkun`, `totalPengeluaran` |
| **Template HTML** | `kebab-case.html` / `camelCase.html` | `beranda.html`, `kartuAkun.html`, `dialogAlokasi.html` |

---

## 3. Struktur Modul & Folder Proyek

```text
abracadabra/
├── AGENTS.md                    # File memori & panduan pengembang
├── backend/
│   ├── database/
│   │   └── app.db               # Database SQLite lokal
│   ├── BasisData/
│   │   ├── basisData.py         # Koneksi engine & session SQLite
│   │   └── skemaTabel.py        # Model tabel database (ORM/SQLAlchemy/SQLModel)
│   ├── KelolaAkun/
│   │   ├── akunModel.py         # Skema data Pydantic akun
│   │   └── akunLayanan.py       # Logika bisnis akun (tambah, edit, ambil saldo)
│   ├── AlokasiDana/
│   │   ├── alokasiModel.py      # Aturan pembagian pemasukan (mingguan/bulanan)
│   │   └── alokasiLayanan.py    # Logika kalkulasi pembagian dana
│   ├── Transaksi/
│   │   ├── transaksiModel.py    # Model pencatatan kas keluar & masuk
│   │   └── transaksiLayanan.py  # Logika pembagian jatah tunai harian & guard buffer
│   └── main.py                  # Entry point FastAPI & routing utama
└── frontend/
    ├── Statis/                  # File statis pendukung (CSS kustom, JS helper)
    │   └── js/
    │       └── aplikasi.js
    └── Template/                # File HTML Jinja2
        ├── dasar.html           # Layout utama (Tailwind + Alpine.js CDN)
        ├── beranda.html         # Halaman dashboard utama
        └── Komponen/
            ├── kartuAkun.html   # Kartu rekening (Tabungan & Operasional)
            ├── dialogAlokasi.html # Wizard pemasukan
            └── pelacakDompet.html # Status jatah makan kos vs digital
```

---

## 4. Konsep Bisnis Inti (SAVETRACK)

1. **Multi-Rekening Fleksibel:**
   - Rekening tabungan bisa lebih dari satu (bebas tambah bank/dompet digital).
   - Nomor rekening bersifat opsional demi menjaga privasi portofolio.
   - Pembeda tipe rekening:
     - `TABUNGAN_TERKUNCI` (Target masa depan / uang dingin)
     - `KAS_OPERASIONAL` (Uang harian & buffer kas darurat)

2. **Mesin Alokasi Pendapatan Dinamis:**
   - Mendukung siklus mingguan (default mahasiswa: Kamis) atau bulanan.
   - Pengguna bebas mengatur formula distribusi (Tabungan Wajib, Dompet Tunai Makan, Bensin, Kuota, Surplus Endapan).

3. **Pelacak Dua Saku (Dual-Pocket Tracker):**
   - **Saku Fisik (Tunai):** Khusus kebutuhan makan harian dengan batas aman per hari (`Saldo Tunai ÷ Sisa Hari Kos`).
   - **Saku Digital (QRIS/Transfer):** Khusus bensin dan kuota internet.
   - **Guard Kas Darurat:** Notifikasi peringatan jika saldo kas operasional menyentuh batas bawah proteksi.

---

## 5. Batasan & Aturan Teknis Agen
- Jangan pernah memasukkan perintah kompilasi `npm` atau `webpack` ke server backend FastAPI.
- Seluruh kode antarmuka menggunakan Tailwind CSS CDN dan Alpine.js CDN.
- Pertahankan nama fungsi dan class dalam Bahasa Indonesia sesuai tabel konvensi di bagian 2.
- Utamakan performa ringan agar dapat dibuka lancar di browser ponsel pintar dan laptop melalui IP lokal.
- **Standar UI & Copywriting (Anti-AI Slop):**
  - Hindari badge/pill kapsul dekoratif mengambang tanpa aksi interaktif.
  - Gunakan label teks judul langsung (contoh: `Batas Belanja Makan Hari Ini`) alih-alih pill buatan AI.
  - Pertahankan tipografi font Satoshi untuk teks dan angka nominal.
