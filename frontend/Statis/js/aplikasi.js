/**
 * SAVEURMONEY - State Management & Logika Finansial
 * Standar Arsitektur:
 * 1. Tanpa modal pop-up: inline tab-based action flow.
 * 2. Pos Digital dihapus: pengeluaran umum langsung memotong Tabungan Operasional.
 * 3. Saku Tunai dipertahankan: batas harian = Saldo Tunai ÷ Sisa Hari Siklus.
 * 4. Target Tabungan Dinamis: Nama, Nominal Sasaran, Tenggat Tanggal, kalkulasi Wajib Simpan/Siklus.
 * 5. Bahasa Sistem Lugas, bebas kata 'Saya', indikator natural tanpa pill slop.
 */

document.addEventListener('alpine:init', () => {
  Alpine.data('aplikasiSaveurMoney', () => ({
    // Navigasi Halaman Utama
    halamanAktif: 'beranda', // 'beranda' | 'rekening' | 'saku' | 'riwayat'
    sidebarBuka: false,
    sidebarCollapsed: false,

    // Tab Aksi Inline di Halaman Beranda
    // Opsi: 'ringkasan' | 'catat' | 'alokasi' | 'transfer' | 'tambahAkun'
    tabAksiAktif: 'ringkasan',

    // Filter Kategori Rekening
    tabKategoriAkun: 'SEMUA', // 'SEMUA' | 'OPERASIONAL' | 'TABUNGAN'

    // Notifikasi Toast
    pesanNotifikasi: '',
    tipeNotifikasi: 'sukses',
    tampilNotifikasi: false,
    timerNotifikasi: null,

    // Konfigurasi Siklus Mahasiswa
    sisaHariKos: 7,

    // Target Tabungan Dinamis (Default Nol)
    targetTabungan: {
      nama: '',
      nominal: 0,
      tenggat: ''
    },

    // Data Rekening (Baku: TABUNGAN_OPERASIONAL & TABUNGAN_UTAMA)
    daftarAkun: [],

    // Saku Fisik (Tunai Kos Khusus Makan Pokok)
    sakuTunai: {
      saldo: 0,
      terpakaiMingguIni: 0
    },
    inputKoreksiTunai: '',

    // Riwayat Transaksi
    riwayatTransaksi: [],

    // Form Tambah / Edit Rekening Inline
    idAkunDiedit: null, // null jika tambah baru, string id jika mode edit
    formAkun: {
      nama: '',
      tipe: 'TABUNGAN_OPERASIONAL',
      kategori: 'Bank Digital',
      nomorRekening: '',
      saldoAwal: ''
    },

    // Form Catat Belanja Inline (Ergonomis)
    formCatat: {
      sumber: 'TABUNGAN_OPERASIONAL', // 'SAKU_TUNAI' | 'TABUNGAN_OPERASIONAL' | id akun spesifik
      kategori: 'Makan & Minum',
      nominal: '',
      catatan: ''
    },

    // Form Pindah Dana Inline
    formTransfer: {
      idDari: '',
      idTujuan: '',
      nominal: '',
      catatan: ''
    },

    // Form Alokasi Pemasukan Langsung ke Satu Rekening
    alokasi: {
      idRekeningTujuan: '',
      kategori: 'Gaji / Kiriman Bulanan',
      totalNominal: '',
      catatan: ''
    },
    batasAmanCadanganInput: 200000,

    // Mode Tema
    modeGelap: false,

    init() {
      // Pembersihan total ke status fresh nol saat dimuat
      if (localStorage.getItem('saveurmoney_versi') !== 'v4_fresh_nol') {
        localStorage.removeItem('saveurmoney_daftarAkun');
        localStorage.removeItem('saveurmoney_sakuTunai');
        localStorage.removeItem('saveurmoney_sakuDigital');
        localStorage.removeItem('saveurmoney_targetTabungan');
        localStorage.removeItem('saveurmoney_sisaHariKos');
        localStorage.removeItem('saveurmoney_riwayat');
        localStorage.setItem('saveurmoney_versi', 'v4_fresh_nol');
      }

      const temaDisimpan = localStorage.getItem('saveurmoney_modeGelap');
      if (temaDisimpan !== null) {
        this.modeGelap = temaDisimpan === 'true';
      } else {
        this.modeGelap = window.matchMedia('(prefers-color-scheme: dark)').matches;
      }
      this.terapkanTema();

      this.muatDataLokal();
          },

    toggleTema() {
      this.modeGelap = !this.modeGelap;
      localStorage.setItem('saveurmoney_modeGelap', this.modeGelap);
      this.terapkanTema();
    },

    terapkanTema() {
      if (this.modeGelap) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    },

    // Navigasi Cepat Tab Aksi Inline
    bukaTabAksi(tab) {
      this.halamanAktif = 'beranda';
      this.tabAksiAktif = tab;
      // Scroll halus ke area aksi jika di layar kecil
      const wadahAksi = document.getElementById('wadah-aksi-inline');
      if (wadahAksi) {
        wadahAksi.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    },

    // Persistensi Data
    simpanDataLokal() {
      try {
        localStorage.setItem('saveurmoney_daftarAkun', JSON.stringify(this.daftarAkun));
        localStorage.setItem('saveurmoney_sakuTunai', JSON.stringify(this.sakuTunai));
        localStorage.setItem('saveurmoney_targetTabungan', JSON.stringify(this.targetTabungan));
        localStorage.setItem('saveurmoney_sisaHariKos', String(this.sisaHariKos));
        localStorage.setItem('saveurmoney_batasAman', String(this.batasAmanCadanganInput));
        localStorage.setItem('saveurmoney_riwayat', JSON.stringify(this.riwayatTransaksi));
      } catch (e) {
        console.warn('Gagal menyimpan ke localStorage:', e);
      }
    },

    muatDataLokal() {
      const akunTersimpan = localStorage.getItem('saveurmoney_daftarAkun');
      const tunaiTersimpan = localStorage.getItem('saveurmoney_sakuTunai');
      const targetTersimpan = localStorage.getItem('saveurmoney_targetTabungan');
      const hariTersimpan = localStorage.getItem('saveurmoney_sisaHariKos');
      const riwayatTersimpan = localStorage.getItem('saveurmoney_riwayat');

      if (akunTersimpan) {
        const raw = JSON.parse(akunTersimpan);
        // Normalisasi tipe ke TABUNGAN_OPERASIONAL & TABUNGAN_UTAMA
        this.daftarAkun = raw.map(a => {
          let tipe = a.tipe;
          if (tipe === 'KAS_OPERASIONAL') tipe = 'TABUNGAN_OPERASIONAL';
          if (tipe === 'TABUNGAN_TERKUNCI') tipe = 'TABUNGAN_UTAMA';
          return { ...a, tipe };
        });
      } else {
        this.daftarAkun = [];
      }

      if (tunaiTersimpan) {
        this.sakuTunai = JSON.parse(tunaiTersimpan);
      } else {
        this.sakuTunai = { saldo: 0, terpakaiMingguIni: 0 };
      }

      if (targetTersimpan) {
        this.targetTabungan = JSON.parse(targetTersimpan);
        if (this.targetTabungan && this.targetTabungan.nominal) this.targetTabungan.nominal = this.formatRibuan(this.targetTabungan.nominal);
      }

      if (hariTersimpan) {
        this.sisaHariKos = Number(hariTersimpan) || 7;
      }
      const batasAmanTersimpan = localStorage.getItem('saveurmoney_batasAman');
      if (batasAmanTersimpan) {
        this.batasAmanCadanganInput = Number(batasAmanTersimpan) || 200000;
      }

      if (riwayatTersimpan) {
        this.riwayatTransaksi = JSON.parse(riwayatTersimpan);
      } else {
        this.riwayatTransaksi = [];
      }
    },

    kirimNotifikasi(pesan, tipe = 'sukses') {
      this.pesanNotifikasi = pesan;
      this.tipeNotifikasi = tipe;
      this.tampilNotifikasi = true;
      if (this.timerNotifikasi) clearTimeout(this.timerNotifikasi);
      this.timerNotifikasi = setTimeout(() => {
        this.tampilNotifikasi = false;
      }, 3000);
    },

    // GETTERS & METRIK KALKULASI
    get akunTerfilter() {
      if (this.tabKategoriAkun === 'OPERASIONAL') {
        return this.daftarAkun.filter(a => a.tipe === 'TABUNGAN_OPERASIONAL');
      }
      if (this.tabKategoriAkun === 'TABUNGAN') {
        return this.daftarAkun.filter(a => a.tipe === 'TABUNGAN_UTAMA');
      }
      return this.daftarAkun;
    },

    get akunOperasionalList() {
      return this.daftarAkun.filter(a => a.tipe === 'TABUNGAN_OPERASIONAL');
    },

    get akunUtamaList() {
      return this.daftarAkun.filter(a => a.tipe === 'TABUNGAN_UTAMA');
    },

    get totalKasOperasional() {
      return this.daftarAkun
        .filter(a => a.tipe === 'TABUNGAN_OPERASIONAL')
        .reduce((sum, a) => sum + Number(a.saldo || 0), 0);
    },

    get totalTabunganUtama() {
      return this.daftarAkun
        .filter(a => a.tipe === 'TABUNGAN_UTAMA')
        .reduce((sum, a) => sum + Number(a.saldo || 0), 0);
    },

    get totalKekayaanBersih() {
      return this.totalKasOperasional + this.totalTabunganUtama + Number(this.sakuTunai.saldo || 0);
    },

    get batasAmanOperasional() {
      return Number(this.batasAmanCadanganInput) || 200000;
    },

    aturBatasAman(nominal) {
      nominal = this.bersihkanAngka(nominal);
      this.batasAmanCadanganInput = Math.max(0, Number(nominal) || 0);
      localStorage.setItem('saveurmoney_batasAman', String(this.batasAmanCadanganInput));
      this.kirimNotifikasi('Batas aman cadangan diubah ke ' + this.formatRupiah(this.batasAmanCadanganInput));
    },

    get selisihBatasAman() {
      return this.totalKasOperasional - this.batasAmanOperasional;
    },

    get isOperasionalDibawahAman() {
      return this.totalKasOperasional < this.batasAmanOperasional;
    },

    // Jatah Harian Makan: Saldo Tunai ÷ Sisa Hari Siklus
    get jatahMakanHarian() {
      const hari = Math.max(1, Number(this.sisaHariKos) || 1);
      const saldo = Math.max(0, Number(this.sakuTunai.saldo) || 0);
      return Math.floor(saldo / hari);
    },

    // Target Tabungan Dinamis & Kalkulasi Wajib Simpan
    get persentaseTargetTabungan() {
      const target = Number(this.targetTabungan.nominal) || 0;
      if (target <= 0) return 0;
      const rasio = (this.totalTabunganUtama / target) * 100;
      return Math.min(100, Math.max(0, Math.round(rasio)));
    },

    get kekuranganTargetTabungan() {
      const target = Number(this.targetTabungan.nominal) || 0;
      return Math.max(0, target - this.totalTabunganUtama);
    },

    get sisaSiklusMenujuTenggat() {
      if (!this.targetTabungan.tenggat) return 4;
      const sekarang = new Date();
      sekarang.setHours(0, 0, 0, 0);
      const target = new Date(this.targetTabungan.tenggat);
      if (isNaN(target.getTime())) return 4;
      const selisihHari = Math.max(1, Math.ceil((target - sekarang) / (1000 * 60 * 60 * 24)));
      // Asumsi 1 siklus = durasi sisaHariKos (default 7 hari)
      const siklus = Math.ceil(selisihHari / (Number(this.sisaHariKos) || 7));
      return Math.max(1, siklus);
    },

    get wajibSimpanPerSiklus() {
      if (this.kekuranganTargetTabungan <= 0) return 0;
      return Math.ceil(this.kekuranganTargetTabungan / this.sisaSiklusMenujuTenggat);
    },

    // HELPER FORMAT & INPUT RUPIAH
    formatRupiah(nilai) {
      const num = Number(nilai) || 0;
      return new Intl.NumberFormat('id-ID', {
        style: 'currency',
        currency: 'IDR',
        maximumFractionDigits: 0
      }).format(num);
    },

    formatRibuan(angka) {
      if (angka === null || angka === undefined || angka === '') return '';
      const bersih = String(angka).replace(/\D/g, '');
      if (!bersih) return '';
      return new Intl.NumberFormat('id-ID').format(Number(bersih));
    },

    bersihkanAngka(teks) {
      if (!teks) return 0;
      return Number(String(teks).replace(/\D/g, '')) || 0;
    },

    onInputSaldoAwal(e) {
      const val = e.target.value;
      const num = this.bersihkanAngka(val);
      const terformat = num ? this.formatRibuan(num) : '';
      this.formAkun.saldoAwal = terformat;
      e.target.value = terformat;
    },

    onInputNominal(e, objek, properti) {
      const val = e.target.value;
      const num = this.bersihkanAngka(val);
      const terformat = num ? this.formatRibuan(num) : '';
      objek[properti] = terformat;
      e.target.value = terformat;
    },

    formatNomorRekening(nomor, terlihat) {
      if (!nomor) return 'Tanpa Nomor';
      if (terlihat) return nomor;
      if (nomor.length <= 4) return '••••';
      return `•••• •••• ${nomor.slice(-4)}`;
    },

    toggleIntipRekening(id) {
      const target = this.daftarAkun.find(a => a.id === id);
      if (target) {
        target.tampilNomor = !target.tampilNomor;
        this.simpanDataLokal();
      }
    },

    ubahSisaHari(selisih) {
      const baru = Math.max(1, (Number(this.sisaHariKos) || 7) + selisih);
      this.sisaHariKos = baru;
      this.simpanDataLokal();
    },

    // KOREKSI SALDO SAKU TUNAI MANUAL SECARA DINAMIS
    aturSaldoSakuTunai(nominalBaru, alasan = 'Penyesuaian Dompet Fisik') {
      nominalBaru = this.bersihkanAngka(nominalBaru);
      const target = Math.max(0, Number(nominalBaru) || 0);
      const saldoLama = Number(this.sakuTunai.saldo) || 0;
      const selisih = target - saldoLama;

      if (selisih === 0) return;

      this.sakuTunai.saldo = target;

      // Catat ke riwayat transaksi agar pengguna tahu uang keluar/masuk ke mana
      this.riwayatTransaksi.unshift({
        id: `trx-${Date.now()}`,
        tanggal: 'Hari ini, baru saja',
        judul: alasan.trim() || (selisih > 0 ? 'Suntikan Tunai' : 'Penyesuaian Uang Tunai'),
        sumber: 'Saku Tunai (Dompet)',
        kategori: selisih > 0 ? 'Pemasukan' : 'Makan Pokok',
        nominal: Math.abs(selisih),
        arah: selisih > 0 ? 'MASUK' : 'KELUAR'
      });

      this.simpanDataLokal();
      this.kirimNotifikasi(`Saldo saku tunai disesuaikan menjadi ${this.formatRupiah(target)}.`);
    },

    // KALKULASI & DISTRIBUSI ALOKASI PEMASUKAN
    setModeAlokasi(mode) {
      this.alokasi.mode = mode;
      if (mode === 'mingguan') {
        this.alokasi.totalNominal = 500000;
      } else {
        this.alokasi.totalNominal = 2000000;
      }
          },

    hitungFormulaAlokasi() {
      const nominal = Math.max(0, Number(this.alokasi.totalNominal) || 0);

      if (this.alokasi.mode === 'mingguan') {
        // Porsi Mingguan:
        // Saku Tunai Makan: 50%
        // Tabungan Utama: 25% (atau sesuaikan dengan wajibSimpanPerSiklus)
        // Kas Operasional: 25%
        this.alokasi.pos.sakuTunaiMakan = Math.round(nominal * 0.50);
        this.alokasi.pos.tabunganUtama = Math.round(nominal * 0.25);
        this.alokasi.pos.kasOperasional = nominal - (this.alokasi.pos.sakuTunaiMakan + this.alokasi.pos.tabunganUtama);
      } else {
        // Porsi Bulanan:
        // Saku Tunai Makan: 40%
        // Tabungan Utama: 30%
        // Kas Operasional: 30%
        this.alokasi.pos.sakuTunaiMakan = Math.round(nominal * 0.40);
        this.alokasi.pos.tabunganUtama = Math.round(nominal * 0.30);
        this.alokasi.pos.kasOperasional = nominal - (this.alokasi.pos.sakuTunaiMakan + this.alokasi.pos.tabunganUtama);
      }
    },

    terapkanAlokasiDana() {
      const nominal = this.bersihkanAngka(this.alokasi.totalNominal);
      if (!nominal || nominal <= 0) {
        this.kirimNotifikasi('Masukkan nominal pemasukan!', 'peringatan');
        return;
      }

      if (!this.alokasi.idRekeningTujuan) {
        this.kirimNotifikasi('Pilih salah satu pos atau rekening tujuan!', 'peringatan');
        return;
      }

      let namaTujuan = '';

      // Opsi 1: Suntikan Masuk ke Dompet Fisik Tunai
      if (this.alokasi.idRekeningTujuan === 'SAKU_TUNAI') {
        this.sakuTunai.saldo = Number(this.sakuTunai.saldo || 0) + nominal;
        namaTujuan = 'Dompet Fisik (Tunai)';
      } 
      // Opsi 2: Masuk ke Rekening Bank / E-Wallet Terpilih
      else {
        const akun = this.daftarAkun.find(a => a.id == this.alokasi.idRekeningTujuan);
        if (!akun) {
          this.kirimNotifikasi('Rekening tujuan tidak ditemukan!', 'bahaya');
          return;
        }
        akun.saldo = Number(akun.saldo || 0) + nominal;
        namaTujuan = akun.nama;
      }

      // Catat Riwayat Transaksi Pemasukan
      const deskripsi = this.alokasi.catatan ? this.alokasi.catatan.trim() : (this.alokasi.kategori || 'Suntikan Dana Masuk');
      this.riwayatTransaksi.unshift({
        id: `trx-${Date.now()}`,
        tanggal: 'Hari ini, baru saja',
        judul: deskripsi,
        sumber: 'Pemasukan Luar',
        kategori: this.alokasi.kategori || 'Pemasukan',
        nominal: nominal,
        arah: 'MASUK'
      });

      this.simpanDataLokal();
      this.alokasi.totalNominal = '';
      this.alokasi.catatan = '';
      this.tabAksiAktif = 'ringkasan';
      this.kirimNotifikasi(`Pemasukan ${this.formatRupiah(nominal)} berhasil masuk ke ${namaTujuan}.`);
    },

    // SIMPAN PENGELUARAN (CATAT BELANJA INLINE)
    simpanTransaksiBelanja() {
      const nominal = this.bersihkanAngka(this.formCatat.nominal);
      if (!nominal || nominal <= 0) {
        this.kirimNotifikasi('Masukkan nominal pengeluaran!', 'peringatan');
        return;
      }

      let labelSumber = '';

      // Jalur 1: Dompet Fisik Tunai
      if (this.formCatat.sumber === 'SAKU_TUNAI') {
        if (this.sakuTunai.saldo < nominal) {
          this.kirimNotifikasi('Saldo dompet fisik tidak cukup!', 'bahaya');
          return;
        }
        this.sakuTunai.saldo -= nominal;
        this.sakuTunai.terpakaiMingguIni += nominal;
        labelSumber = 'Dompet Fisik';
      }
      // Jalur 2: Tabungan Operasional
      else if (this.formCatat.sumber === 'TABUNGAN_OPERASIONAL') {
        let akunOps = this.akunOperasionalList[0];
        if (!akunOps) {
          this.kirimNotifikasi('Belum ada rekening Tabungan Operasional!', 'peringatan');
          return;
        }
        if (akunOps.saldo < nominal) {
          this.kirimNotifikasi(`Saldo di ${akunOps.nama} tidak mencukupi!`, 'bahaya');
          return;
        }
        akunOps.saldo -= nominal;
        labelSumber = akunOps.nama;
      }
      // Jalur 3: Tabungan Utama
      else if (this.formCatat.sumber === 'TABUNGAN_UTAMA') {
        let akunUtama = this.akunUtamaList[0];
        if (!akunUtama) {
          this.kirimNotifikasi('Belum ada rekening Tabungan Utama!', 'peringatan');
          return;
        }
        if (akunUtama.saldo < nominal) {
          this.kirimNotifikasi(`Saldo di ${akunUtama.nama} tidak mencukupi!`, 'bahaya');
          return;
        }
        akunUtama.saldo -= nominal;
        labelSumber = akunUtama.nama;
      }
      // Jalur 4: Rekening Spesifik yang Dipilih lewat Dropdown
      else {
        const akun = this.daftarAkun.find(a => a.id == this.formCatat.sumber);
        if (!akun) {
          this.kirimNotifikasi('Pilih sumber dana yang sah!', 'peringatan');
          return;
        }
        if (akun.saldo < nominal) {
          this.kirimNotifikasi(`Saldo di ${akun.nama} tidak mencukupi!`, 'bahaya');
          return;
        }
        akun.saldo -= nominal;
        labelSumber = akun.nama;
      }

      // Catat ke riwayat
      const judulTransaksi = this.formCatat.catatan.trim() || this.formCatat.kategori;
      this.riwayatTransaksi.unshift({
        id: `trx-${Date.now()}`,
        tanggal: 'Hari ini, baru saja',
        judul: judulTransaksi,
        sumber: labelSumber,
        kategori: this.formCatat.kategori,
        nominal: nominal,
        arah: 'KELUAR'
      });

      this.simpanDataLokal();

      // Reset form
      this.formCatat.nominal = '';
      this.formCatat.catatan = '';
      this.tabAksiAktif = 'ringkasan';
      this.kirimNotifikasi(`Pengeluaran ${this.formatRupiah(nominal)} berhasil dicatat.`);
    },

    // TAMBAH / EDIT REKENING INLINE
    mulaiEditRekening(id) {
      const akun = this.daftarAkun.find(a => a.id === id);
      if (!akun) return;
      this.idAkunDiedit = akun.id;
      this.formAkun = {
        nama: akun.nama,
        tipe: akun.tipe,
        kategori: akun.kategori,
        nomorRekening: akun.nomorRekening || '',
        saldoAwal: this.formatRibuan(akun.saldo)
      };
      this.bukaTabAksi('tambahAkun');
    },

    batalFormAkun() {
      this.idAkunDiedit = null;
      this.formAkun = {
        nama: '',
        tipe: 'TABUNGAN_OPERASIONAL',
        kategori: 'Bank Digital',
        nomorRekening: '',
        saldoAwal: ''
      };
      this.tabAksiAktif = 'ringkasan';
    },

    simpanRekeningBaru() {
      if (!this.formAkun.nama.trim()) {
        this.kirimNotifikasi('Nama rekening wajib diisi!', 'peringatan');
        return;
      }

      const saldoNominal = this.bersihkanAngka(this.formAkun.saldoAwal);

      // Mode Update Rekening Eksisting
      if (this.idAkunDiedit) {
        const akun = this.daftarAkun.find(a => a.id === this.idAkunDiedit);
        if (akun) {
          const saldoLama = Number(akun.saldo) || 0;
          const selisih = saldoNominal - saldoLama;

          akun.nama = this.formAkun.nama.trim();
          akun.tipe = this.formAkun.tipe;
          akun.kategori = this.formAkun.kategori;
          akun.nomorRekening = this.formAkun.nomorRekening.trim();
          akun.saldo = saldoNominal;
          akun.keterangan = akun.tipe === 'TABUNGAN_UTAMA'
            ? 'Pos dana dingin dan sasaran masa depan'
            : 'Buffer kas operasional dan transaksi harian';
          
          // CATAT KE MUTASI JIKA ADA PERUBAHAN SALDO MANUAL
          if (selisih !== 0) {
            this.riwayatTransaksi.unshift({
              id: `trx-${Date.now()}`,
              tanggal: 'Hari ini, baru saja',
              judul: `Penyesuaian Saldo: ${akun.nama} (${selisih > 0 ? '+' : ''}${this.formatRupiah(selisih)})`,
              sumber: selisih > 0 ? 'Koreksi Saldo (+)' : akun.nama,
              kategori: 'Penyesuaian Saldo',
              nominal: Math.abs(selisih),
              arah: selisih > 0 ? 'MASUK' : 'KELUAR'
            });
          }

          this.simpanDataLokal();
          this.batalFormAkun();
          this.kirimNotifikasi(`Perubahan rekening ${akun.nama} berhasil disimpan.`);
          return;
        }
      }

      // Mode Tambah Rekening Baru
      const akunBaru = {
        id: `rek-${Date.now()}`,
        nama: this.formAkun.nama.trim(),
        tipe: this.formAkun.tipe, // 'TABUNGAN_OPERASIONAL' | 'TABUNGAN_UTAMA'
        kategori: this.formAkun.kategori,
        nomorRekening: this.formAkun.nomorRekening.trim(),
        saldo: saldoNominal,
        tampilNomor: false,
        keterangan: this.formAkun.tipe === 'TABUNGAN_UTAMA'
          ? 'Pos dana dingin dan sasaran masa depan'
          : 'Buffer kas operasional dan transaksi harian'
      };

      this.daftarAkun.push(akunBaru);

      // Catat ke transaksi jika saldo awal > 0
      if (saldoNominal > 0) {
        this.riwayatTransaksi.unshift({
          id: `trx-${Date.now()}`,
          tanggal: 'Hari ini, baru saja',
          judul: `Saldo Awal: ${akunBaru.nama}`,
          sumber: 'Pendaftaran Akun',
          kategori: 'Saldo Awal',
          nominal: saldoNominal,
          arah: 'MASUK'
        });
      }

      this.simpanDataLokal();
      this.batalFormAkun();
      this.kirimNotifikasi(`Rekening ${akunBaru.nama} berhasil ditambahkan.`);
    },

    hapusRekening(id) {
      const target = this.daftarAkun.find(a => a.id === id);
      if (!target) return;
      if (confirm(`Hapus rekening "${target.nama}"?`)) {
        this.daftarAkun = this.daftarAkun.filter(a => a.id !== id);
        this.simpanDataLokal();
        this.kirimNotifikasi(`Rekening "${target.nama}" telah dihapus.`, 'info');
      }
    },

    // PINDAH DANA INLINE
    eksekusiTransferInline() {
      const nominal = this.bersihkanAngka(this.formTransfer.nominal);
      if (!nominal || nominal <= 0) {
        this.kirimNotifikasi('Masukkan nominal pindah dana!', 'peringatan');
        return;
      }
      if (!this.formTransfer.idDari || !this.formTransfer.idTujuan) {
        this.kirimNotifikasi('Pilih rekening asal dan rekening tujuan!', 'peringatan');
        return;
      }
      if (this.formTransfer.idDari === this.formTransfer.idTujuan) {
        this.kirimNotifikasi('Rekening asal dan tujuan tidak boleh sama!', 'peringatan');
        return;
      }

      const asal = this.daftarAkun.find(a => a.id === this.formTransfer.idDari);
      const tujuan = this.daftarAkun.find(a => a.id === this.formTransfer.idTujuan);

      if (!asal || !tujuan) {
        this.kirimNotifikasi('Data rekening tidak ditemukan!', 'peringatan');
        return;
      }

      if (asal.saldo < nominal) {
        this.kirimNotifikasi(`Saldo di ${asal.nama} tidak mencukupi!`, 'bahaya');
        return;
      }

      asal.saldo -= nominal;
      tujuan.saldo += nominal;

      this.riwayatTransaksi.unshift({
        id: `trx-${Date.now()}`,
        tanggal: 'Hari ini, baru saja',
        judul: `Pindah Dana: ${asal.nama} → ${tujuan.nama}`,
        sumber: 'Internal Transfer',
        kategori: 'Transfer',
        nominal: nominal,
        arah: 'TRANSFER'
      });

      this.simpanDataLokal();
      this.formTransfer = { idDari: '', idTujuan: '', nominal: '', catatan: '' };
      this.tabAksiAktif = 'ringkasan';
      this.kirimNotifikasi(`Berhasil memindahkan ${this.formatRupiah(nominal)} ke ${tujuan.nama}.`);
    },

    // PERBARUI TARGET TABUNGAN DINAMIS
    simpanTargetTabungan() {
      if (!this.targetTabungan.nama.trim()) {
        this.targetTabungan.nama = 'Target Finansial';
      }
      this.targetTabungan.nominal = Math.max(0, this.bersihkanAngka(this.targetTabungan.nominal));
      this.simpanDataLokal();
      this.kirimNotifikasi('Target tabungan berhasil diperbarui.');
    },

    // EKSEKUSI RESET TOTAL (DIPANGGIL DARI VALIDASI INLINE SIDEBAR)
    eksekusiResetTotal() {
      this.daftarAkun = [];
      this.sakuTunai = { saldo: 0, terpakaiMingguIni: 0 };
      this.targetTabungan = { nama: '', nominal: 0, tenggat: '' };
      this.sisaHariKos = 7;
      this.riwayatTransaksi = [];
      this.batalFormAkun();
      this.simpanDataLokal();
      this.kirimNotifikasi('Semua data berhasil dibersihkan ke kondisi nol.', 'info');
    },

    // EKSPOR PDF RIWAYAT TRANSAKSI (NOL DEPENDENSI SERVER / ZERO BUNDLER)
    eksporPDFRiwayat() {
      if (this.riwayatTransaksi.length === 0) {
        this.kirimNotifikasi('Belum ada riwayat transaksi untuk diekspor!', 'peringatan');
        return;
      }

      const barisTabel = this.riwayatTransaksi.map((t, idx) => `
        <tr>
          <td style="padding: 8px; border-bottom: 1px solid #e2e6ec; text-align: center;">${idx + 1}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e2e6ec;">${t.tanggal}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e2e6ec; font-weight: 600;">${t.judul}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e2e6ec;">${t.kategori}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e2e6ec;">${t.sumber}</td>
          <td style="padding: 8px; border-bottom: 1px solid #e2e6ec; text-align: right; font-weight: 700; color: ${t.arah === 'MASUK' ? '#191970' : (t.arah === 'TRANSFER' ? '#24248A' : '#FB5607')};">
            ${t.arah === 'MASUK' ? '+' : (t.arah === 'TRANSFER' ? '' : '-')}${this.formatRupiah(t.nominal)}
          </td>
        </tr>
      `).join('');

      const totalMasuk = this.riwayatTransaksi.filter(t => t.arah === 'MASUK').reduce((acc, t) => acc + Number(t.nominal), 0);
      const totalKeluar = this.riwayatTransaksi.filter(t => t.arah === 'KELUAR').reduce((acc, t) => acc + Number(t.nominal), 0);

      const jendelaCetak = window.open('', '_blank');
      jendelaCetak.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>Laporan Transaksi - SAVEURMONEY</title>
          <style>
            body { font-family: 'Inter', -apple-system, sans-serif; padding: 25px; color: #191970; }
            h2 { margin: 0; font-size: 20px; color: #191970; }
            p { margin: 4px 0 16px 0; font-size: 12px; color: #666; }
            table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 10px; }
            th { background-color: #f1f3f6; color: #24248A; text-align: left; padding: 8px; border-bottom: 2px solid #cbd5e1; }
            .ringkasan { margin-top: 20px; display: flex; justify-content: flex-end; gap: 20px; font-size: 13px; }
            .box { padding: 10px 15px; border-radius: 6px; background: #f8f9fb; border: 1px solid #e2e6ec; }
            @media print {
              body { padding: 0; }
              @page { size: auto; margin: 15mm; }
            }
          </style>
        </head>
        <body>
          <div style="display: flex; justify-content: space-between; align-items: baseline; border-bottom: 2px solid #FB5607; padding-bottom: 8px;">
            <div>
              <h2>SAVEURMONEY - LAPORAN KEUANGAN</h2>
              <p>Dicetak pada: ${new Date().toLocaleDateString('id-ID', { dateStyle: 'full' })}</p>
            </div>
            <div style="text-align: right; font-size: 12px; font-weight: bold; color: #24248A;">
              Total Riwayat: ${this.riwayatTransaksi.length} Transaksi
            </div>
          </div>

          <table>
            <thead>
              <tr>
                <th style="width: 30px; text-align: center;">No</th>
                <th>Waktu</th>
                <th>Transaksi / Deskripsi</th>
                <th>Kategori</th>
                <th>Sumber Dana</th>
                <th style="text-align: right;">Nominal</th>
              </tr>
            </thead>
            <tbody>
              ${barisTabel}
            </tbody>
          </table>

          <div class="ringkasan">
            <div class="box">Total Pemasukan: <strong style="color: #191970;">+${this.formatRupiah(totalMasuk)}</strong></div>
            <div class="box">Total Pengeluaran: <strong style="color: #FB5607;">-${this.formatRupiah(totalKeluar)}</strong></div>
          </div>

          <script>
            window.onload = function() {
              window.print();
            };
          </script>
        </body>
        </html>
      `);
      jendelaCetak.document.close();
    }
  }));
});
