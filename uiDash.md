# Pengetahuan Komponen & Layout UI (Referensi Dash-UI)

Dokumen ini berisi ekstraksi pola desain, tata letak, dan arsitektur komponen dari **Dash-UI** yang diterjemahkan langsung ke dalam arsitektur **SAVETRACK** tanpa Bootstrap, menggunakan **Tailwind CSS (CDN)** dan **Alpine.js (CDN)** sesuai aturan proyek (`AGENTS.md`).

---

## 1. Arsitektur Layout Utama (App Shell)

Dash-UI menggunakan struktur `db-wrapper`:
- **Sidebar Kiri (Vertical Nav):** Menempel di sisi kiri (`w-64` atau mode ringkas `w-18`), berisi logo brand, heading grup menu, dan daftar navigasi item dengan indikator aktif.
- **Top Header Bar:** Bar navigasi atas berisi tombol toggle sidebar, bilah pencarian instan, notifikasi dropdown, dan avatar profil pengguna.
- **Hero/Accent Banner Header:** Area latar belakang atas (`bg-tema-dasar` / `bg-primary`) yang memberi kedalaman visual sebelum grid konten.
- **Konten Mengambang (Negative Margin / Floating Canvas):** Kontainer kartu metrik yang naik sedikit (`-mt-12` s.d `-mt-16`) di atas banner sehingga tampak elegan dan modern.

### Implementasi Tailwind + Alpine.js:
```html
<div class="flex h-screen overflow-hidden bg-canvas dark:bg-canvas-dark">
  <!-- Sidebar -->
  <aside class="fixed inset-y-0 left-0 z-50 flex flex-col border-r border-border bg-surface transition-all duration-200 lg:static">
    <!-- Brand & Navigasi -->
  </aside>

  <!-- Area Konten Utama -->
  <div class="flex flex-1 flex-col overflow-y-auto">
    <!-- Header Topbar -->
    <header class="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-surface/90 px-6 backdrop-blur-md">
      <!-- Search & Quick Action -->
    </header>

    <!-- Konten Dashboard -->
    <main class="flex-1 p-6 space-y-6">
      <!-- Grid KPI Metrik -->
    </main>
  </div>
</div>
```

---

## 2. Pola Kartu KPI / Metrik (Hero Metric Cards)

Di Dash-UI, kartu metrik memiliki hierarki:
1. **Header Metrik:** Label teks kategori (kapital/subtle) di kiri dan ikon berbentuk badge bulat/persegi tumpul (`icon-shape`) di kanan atas.
2. **Nilai Utama (Nominal):** Tipografi tebal mencolok (`text-2xl` / `text-3xl font-bold`) dengan angka tabular (`tabular-nums`).
3. **Keterangan & Tren (Contextual Footer):** Keterangan tambahan atau perbandingan persentase dengan warna semantik hijau/merah/netral.

### Implementasi Tailwind:
```html
<div class="rounded-xl border border-border bg-surface p-5 shadow-xs transition hover:border-tema-toska/50 dark:border-border-dark dark:bg-surface-dark">
  <div class="flex items-center justify-between">
    <span class="text-xs font-semibold uppercase tracking-wider text-gray-500">Batas Belanja Makan Hari Ini</span>
    <div class="flex h-10 w-10 items-center justify-center rounded-lg bg-tema-toska/10 text-tema-toska">
      <!-- Icon SVG 20x20 -->
    </div>
  </div>
  <div class="mt-3 text-2xl font-bold text-tema-dasar dark:text-white tabular-nums">
    Rp 45.000
  </div>
  <div class="mt-2 flex items-center justify-between text-xs text-gray-500">
    <span>Saldo Tunai: <strong class="text-tema-toska">Rp 315.000</strong></span>
    <span class="font-medium text-tema-terakota">7 hari tersisa</span>
  </div>
</div>
```

---

## 3. Komponen Data Tables (Tabel Transaksi & Rekening)

Karakteristik tabel Dash-UI:
- Kartu pembungkus dengan header kartu terpisah (`border-b border-border`).
- Baris tabel bersih dengan padding vertikal nyaman (`py-3.5 px-4`).
- Header tabel huruf kapital kecil (`text-[11px] font-semibold tracking-wider text-gray-400 uppercase`).
- Efek hover baris halus (`hover:bg-surface-subtle/60`).
- Badge status berbentuk pil minimalis dengan dot indikator warna.

### Implementasi Tailwind:
```html
<div class="overflow-hidden rounded-xl border border-border bg-surface dark:border-border-dark dark:bg-surface-dark">
  <div class="flex items-center justify-between border-b border-border px-5 py-4 dark:border-border-dark">
    <h3 class="text-sm font-bold text-tema-dasar dark:text-white">Riwayat Transaksi Terakhir</h3>
    <a href="#" class="text-xs font-medium text-tema-toska hover:underline">Lihat Semua</a>
  </div>
  <div class="overflow-x-auto">
    <table class="w-full text-left text-xs">
      <thead class="border-b border-border bg-surface-subtle text-[11px] font-semibold uppercase text-gray-500 dark:border-border-dark dark:bg-surface-dark-subtle dark:text-gray-400">
        <tr>
          <th class="px-5 py-3">Transaksi</th>
          <th class="px-5 py-3">Kategori</th>
          <th class="px-5 py-3">Rekening / Saku</th>
          <th class="px-5 py-3 text-right">Nominal</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-border dark:divide-border-dark">
        <tr class="hover:bg-surface-subtle/50 transition">
          <td class="px-5 py-3.5 font-medium text-tema-dasar dark:text-white">Makan Warteg</td>
          <td class="px-5 py-3.5 text-gray-500">Makan Harian</td>
          <td class="px-5 py-3.5"><span class="rounded bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">Saku Tunai</span></td>
          <td class="px-5 py-3.5 text-right font-bold text-rose-600 tabular-nums">-Rp 15.000</td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
```

---

## 4. Komponen Tab Navigasi & Form Wizard (Segmented Controls)

Pengganti modal bertumpuk sesuai prinsip SAVETRACK & Dash-UI:
- Kontrol tab horizontal dengan transisi aktif tanpa reload (`Alpine.js`).
- Form input terpadu dengan label jelas, icon prefix, dan validasi visual.

---

## 5. Ringkasan Mapping Kelas Bootstrap ke Tailwind CSS

| Komponen Dash-UI (Bootstrap) | Implementasi Tailwind CSS di SAVETRACK |
| :--- | :--- |
| `.card` | `rounded-xl border border-border bg-surface shadow-xs dark:bg-surface-dark` |
| `.card-header` | `flex items-center justify-between border-b border-border px-5 py-4` |
| `.card-body` | `p-5` |
| `.btn.btn-primary` | `rounded-lg bg-tema-toska px-4 py-2 text-xs font-bold text-white hover:bg-tema-toska-hover transition` |
| `.btn.btn-outline-secondary` | `rounded-lg border border-border bg-transparent px-3 py-1.5 text-xs font-medium hover:border-gray-400 transition` |
| `.badge.bg-light-primary` | `rounded-md bg-tema-toska/10 px-2 py-0.5 text-xs font-medium text-tema-toska` |
| `.table` & `.table-hover` | `w-full text-left divide-y divide-border [&_tr:hover]:bg-surface-subtle/50` |
| `.modal` | Modal pop-up diubah menjadi Inline Drawer/Tabs interaktif via `x-show` Alpine.js |

Dokumen ini menjadi acuan baku dalam merancang dan memodifikasi komponen antarmuka SAVETRACK.
