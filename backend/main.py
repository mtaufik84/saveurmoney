"""
SAVEURMONEY Backend API - FastAPI Entrypoint
Standar Arsitektur Sesuai AGENTS.md & PRD-SAVEURMONEY.md
"""
import sys
from pathlib import Path
from typing import List

# Pastikan root proyek masuk ke sys.path saat dijalankan dari direktori manapun
direktoriRoot = Path(__file__).resolve().parent.parent
if str(direktoriRoot) not in sys.path:
    sys.path.insert(0, str(direktoriRoot))

from fastapi import FastAPI, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from backend.Otentikasi import (
    DaftarAdminSkema,
    MasukAdminSkema,
    cekApakahAdminSudahAda,
    daftarkanAdminTunggal,
    otentikasiAdmin,
    buatTokenSesi,
    verifikasiTokenSesi
)

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# Import Basis Data & Skema
from backend.BasisData import (
    mesinBasisData,
    BasisTabel,
    ambilSesiBasisData
)

# Import Layanan KelolaAkun
from backend.KelolaAkun import (
    AkunBuatSkema,
    AkunUbahSkema,
    AkunResponSkema,
    ambilDaftarAkun,
    buatAkunBaru,
    perbaruiAkun,
    hapusAkun,
    ambilBatasAmanCadangan,
    aturBatasAmanCadangan
)

# Import Layanan AlokasiDana
from backend.AlokasiDana import (
    AlokasiBuatSkema,
    prosesAlokasiDana
)

# Import Layanan Transaksi, Saku Tunai, Target Tabungan
from backend.Transaksi import (
    TransaksiBuatSkema,
    TransaksiResponSkema,
    PindahDanaSkema,
    SakuTunaiUbahSkema,
    SakuTunaiResponSkema,
    TargetTabunganBuatSkema,
    TargetTabunganUbahSkema,
    TargetTabunganResponSkema,
    PengaturanBatasAmanSkema,
    ambilAtauBuatSakuTunai,
    perbaruiSakuTunai,
    catatTransaksi,
    ambilDaftarTransaksi,
    prosesPindahDana,
    ambilDaftarTarget,
    buatTargetTabungan,
    perbaruiTargetTabungan,
    ambilRingkasanKPI,
    inisialisasiSeedAwal,
    resetDataDatabase,
    hitungBatasMakanHarian
)

# Inisialisasi tabel di database SQLite saat startup
BasisTabel.metadata.create_all(bind=mesinBasisData)

# Otomatis isi seed data awal jika database baru
with Session(mesinBasisData) as sesiAwal:
    inisialisasiSeedAwal(sesiAwal)

direktoriDasar = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="SAVEURMONEY API",
    description="Backend Manajemen Keuangan Multi-Rekening Mahasiswa/Personal v3.0",
    version="3.0.0"
)

# Mounting folder statis
# Mounting folder public untuk logo & aset gambar
app.mount(
    "/frontend/Public",
    StaticFiles(directory=str(direktoriDasar / "frontend" / "Public")),
    name="public",
)

app.mount(
    "/frontend/Statis",
    StaticFiles(directory=str(direktoriDasar / "frontend" / "Statis")),
    name="statis",
)

# Templating Jinja2
templates = Jinja2Templates(directory=str(direktoriDasar / "frontend" / "Template"))


# ==========================================
# 1. RUTE HALAMAN UTAMA (JINJA2)
# ==========================================


# ==========================================
# 0. RUTE OTENTIKASI & LIVE DEMO
# ==========================================

@app.get("/masuk", response_class=HTMLResponse, tags=["Otentikasi"])
async def halamanMasuk(request: Request, db: Session = Depends(ambilSesiBasisData)):
    adminAda = cekApakahAdminSudahAda(db)
    token = request.cookies.get("sesi_admin")
    if token and verifikasiTokenSesi(token):
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(
        request=request,
        name="masuk.html",
        context={"admin_ada": adminAda, "mode_awal": "masuk" if adminAda else "daftar"}
    )


@app.get("/demo", response_class=HTMLResponse, tags=["Live Demo"])
async def halamanLiveDemo(request: Request):
    """Halaman demonstrasi publik tanpa proteksi login."""
    return templates.TemplateResponse(
        request=request,
        name="demo.html"
    )


@app.post("/api/otentikasi/daftar", tags=["Otentikasi"])
def apiDaftarAdmin(payload: DaftarAdminSkema, db: Session = Depends(ambilSesiBasisData)):
    try:
        adminBaru = daftarkanAdminTunggal(db, payload)
        token = buatTokenSesi(adminBaru.id, adminBaru.namaPengguna)
        response = JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"pesan": "Registrasi admin berhasil", "namaPengguna": adminBaru.namaPengguna}
        )
        response.set_cookie(
            key="sesi_admin",
            value=token,
            httponly=True,
            max_age=60 * 60 * 24 * 7,  # 7 hari
            samesite="lax"
        )
        return response
    except ValueError as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(e)})


@app.post("/api/otentikasi/masuk", tags=["Otentikasi"])
def apiMasukAdmin(payload: MasukAdminSkema, db: Session = Depends(ambilSesiBasisData)):
    admin = otentikasiAdmin(db, payload)
    if not admin:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Nama pengguna atau kata sandi tidak valid"}
        )

    token = buatTokenSesi(admin.id, admin.namaPengguna)
    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"pesan": "Masuk berhasil", "namaPengguna": admin.namaPengguna}
    )
    response.set_cookie(
        key="sesi_admin",
        value=token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax"
    )
    return response


@app.get("/api/otentikasi/keluar", tags=["Otentikasi"])
def apiKeluarAdmin():
    response = RedirectResponse(url="/masuk", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("sesi_admin")
    return response


@app.get("/api/otentikasi/status", tags=["Otentikasi"])
def apiStatusOtentikasi(request: Request, db: Session = Depends(ambilSesiBasisData)):
    adminAda = cekApakahAdminSudahAda(db)
    token = request.cookies.get("sesi_admin")
    namaPengguna = verifikasiTokenSesi(token) if token else None
    return {
        "adminSudahDaftar": adminAda,
        "terotentikasi": namaPengguna is not None,
        "namaPengguna": namaPengguna
    }


@app.get("/", response_class=HTMLResponse, tags=["Antarmuka"])
async def halamanUtama(request: Request, db: Session = Depends(ambilSesiBasisData)):
    adminAda = cekApakahAdminSudahAda(db)
    if not adminAda:
        # Jika belum ada akun pemilik, arahkan ke registrasi awal
        return RedirectResponse(url="/masuk", status_code=status.HTTP_302_FOUND)

    token = request.cookies.get("sesi_admin")
    namaPengguna = verifikasiTokenSesi(token) if token else None
    if not namaPengguna:
        # Belum login wajib masuk ke halaman login dulu
        return RedirectResponse(url="/masuk", status_code=status.HTTP_302_FOUND)

    return templates.TemplateResponse(
        request=request,
        name="beranda.html",
        context={"nama_admin": namaPengguna}
    )


# ==========================================
# 2. RUTE RINGKASAN KPI DASBOR
# ==========================================

@app.get("/api/ringkasan", tags=["Dasbor"])
def apiAmbilRingkasan(db: Session = Depends(ambilSesiBasisData)):
    """
    Mengambil status 3 Hero KPI:
    - Batas Belanja Makan Hari Ini
    - Total Kas Operasional
    - Total Tabungan Utama
    - Batas Aman Cadangan (Dinamis)
    - Indikator Status Darurat
    """
    return ambilRingkasanKPI(db)


# ==========================================
# 3. RUTE KELOLA AKUN REKENING
# ==========================================

@app.get("/api/akun", response_model=List[AkunResponSkema], tags=["Kelola Akun"])
def apiAmbilDaftarAkun(db: Session = Depends(ambilSesiBasisData)):
    return ambilDaftarAkun(db)


@app.post("/api/akun", response_model=AkunResponSkema, status_code=status.HTTP_201_CREATED, tags=["Kelola Akun"])
def apiBuatAkun(payload: AkunBuatSkema, db: Session = Depends(ambilSesiBasisData)):
    return buatAkunBaru(db, payload)


@app.put("/api/akun/{idAkun}", response_model=AkunResponSkema, tags=["Kelola Akun"])
def apiPerbaruiAkun(idAkun: int, payload: AkunUbahSkema, db: Session = Depends(ambilSesiBasisData)):
    return perbaruiAkun(db, idAkun, payload)


@app.delete("/api/akun/{idAkun}", tags=["Kelola Akun"])
def apiHapusAkun(idAkun: int, db: Session = Depends(ambilSesiBasisData)):
    return hapusAkun(db, idAkun)


# ==========================================
# 4. RUTE TARGET TABUNGAN DINAMIS
# ==========================================

@app.get("/api/target", response_model=List[TargetTabunganResponSkema], tags=["Target Tabungan"])
def apiAmbilDaftarTarget(db: Session = Depends(ambilSesiBasisData)):
    return ambilDaftarTarget(db)


@app.post("/api/target", response_model=TargetTabunganResponSkema, status_code=status.HTTP_201_CREATED, tags=["Target Tabungan"])
def apiBuatTarget(payload: TargetTabunganBuatSkema, db: Session = Depends(ambilSesiBasisData)):
    return buatTargetTabungan(db, payload)


@app.put("/api/target/{idTarget}", response_model=TargetTabunganResponSkema, tags=["Target Tabungan"])
def apiPerbaruiTarget(idTarget: int, payload: TargetTabunganUbahSkema, db: Session = Depends(ambilSesiBasisData)):
    return perbaruiTargetTabungan(db, idTarget, payload)


# ==========================================
# 5. RUTE SAKU TUNAI (MAKAN POKOK)
# ==========================================

@app.get("/api/saku-tunai", response_model=SakuTunaiResponSkema, tags=["Saku Tunai"])
def apiAmbilSakuTunai(db: Session = Depends(ambilSesiBasisData)):
    saku = ambilAtauBuatSakuTunai(db)
    return {
        "id": saku.id,
        "saldoTunai": saku.saldoTunai,
        "durasiHariKos": saku.durasiHariKos,
        "batasMakanHarian": hitungBatasMakanHarian(saku.saldoTunai, saku.durasiHariKos)
    }


@app.put("/api/saku-tunai", response_model=SakuTunaiResponSkema, tags=["Saku Tunai"])
def apiPerbaruiSakuTunai(payload: SakuTunaiUbahSkema, db: Session = Depends(ambilSesiBasisData)):
    return perbaruiSakuTunai(db, payload)


# ==========================================
# 6. RUTE ALOKASI PEMASUKAN LANGSUNG KE SATU REKENING
# ==========================================

@app.post("/api/alokasi", tags=["Alokasi Dana"])
def apiProsesAlokasi(payload: AlokasiBuatSkema, db: Session = Depends(ambilSesiBasisData)):
    """
    Mencatat pemasukan masuk langsung ke SATU rekening yang dipilih pengguna.
    Saldo fisik saku tunai tetap independen sesuai kondisi riil di dompet.
    """
    return prosesAlokasiDana(db, payload)


# ==========================================
# 7. RUTE TRANSAKSI & PINDAH DANA
# ==========================================

@app.get("/api/transaksi", response_model=List[TransaksiResponSkema], tags=["Transaksi"])
def apiAmbilDaftarTransaksi(limit: int = 100, db: Session = Depends(ambilSesiBasisData)):
    return ambilDaftarTransaksi(db, limit)


@app.post("/api/transaksi", response_model=TransaksiResponSkema, status_code=status.HTTP_201_CREATED, tags=["Transaksi"])
def apiCatatTransaksi(payload: TransaksiBuatSkema, db: Session = Depends(ambilSesiBasisData)):
    return catatTransaksi(db, payload)


@app.post("/api/pindah-dana", tags=["Transaksi"])
def apiProsesPindahDana(payload: PindahDanaSkema, db: Session = Depends(ambilSesiBasisData)):
    return prosesPindahDana(db, payload)


# ==========================================
# 8. RUTE PENGATURAN BATAS AMAN DINAMIS
# ==========================================

@app.get("/api/pengaturan/batas-aman", tags=["Pengaturan"])
def apiAmbilBatasAman(db: Session = Depends(ambilSesiBasisData)):
    return {"batasAmanCadangan": ambilBatasAmanCadangan(db)}


@app.put("/api/pengaturan/batas-aman", tags=["Pengaturan"])
def apiPerbaruiBatasAman(payload: PengaturanBatasAmanSkema, db: Session = Depends(ambilSesiBasisData)):
    nominal = aturBatasAmanCadangan(db, payload.batasAmanCadangan)
    return {
        "status": "sukses",
        "batasAmanCadangan": nominal,
        "pesan": f"Batas aman cadangan berhasil diatur ke Rp{nominal:,.0f}"
    }


# ==========================================
# 9. RUTE RESET DATA
# ==========================================

@app.post("/api/reset-data", tags=["Pengembang"])
def apiResetData(db: Session = Depends(ambilSesiBasisData)):
    """
    Mengembalikan database ke status awal seed v3.0.
    """
    return resetDataDatabase(db)
