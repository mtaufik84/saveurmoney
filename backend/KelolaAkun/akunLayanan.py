"""
Logika bisnis dan layanan modul KelolaAkun.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.BasisData.skemaTabel import AkunKeuangan, PengaturanAplikasi, TransaksiKeuangan
from .akunModel import AkunBuatSkema, AkunUbahSkema

BATAS_AMAN_DEFAULT = 200000.0


def ambilBatasAmanCadangan(db: Session) -> float:
    pengaturan = db.query(PengaturanAplikasi).filter(
        PengaturanAplikasi.kunci == "batasAmanCadangan"
    ).first()
    if pengaturan:
        try:
            return float(pengaturan.nilai)
        except (ValueError, TypeError):
            return BATAS_AMAN_DEFAULT
    return BATAS_AMAN_DEFAULT


def aturBatasAmanCadangan(db: Session, nominalBaru: float) -> float:
    nominal = max(0.0, float(nominalBaru))
    pengaturan = db.query(PengaturanAplikasi).filter(
        PengaturanAplikasi.kunci == "batasAmanCadangan"
    ).first()
    if not pengaturan:
        pengaturan = PengaturanAplikasi(
            kunci="batasAmanCadangan",
            nilai=str(nominal)
        )
        db.add(pengaturan)
    else:
        pengaturan.nilai = str(nominal)
    db.commit()
    return nominal


def validasiTipeAkun(tipeAkun: str) -> None:
    tipeValid = {"TABUNGAN_UTAMA", "TABUNGAN_OPERASIONAL"}
    if tipeAkun not in tipeValid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipe akun tidak valid. Harus salah satu dari {tipeValid}"
        )


def pasangStatusPeringatan(akun: AkunKeuangan, batasAman: float) -> dict:
    data = {
        "id": akun.id,
        "namaAkun": akun.namaAkun,
        "namaBank": akun.namaBank,
        "nomorRekening": akun.nomorRekening,
        "tipeAkun": akun.tipeAkun,
        "saldo": akun.saldo,
        "terkunci": akun.terkunci,
        "statusDarurat": False,
        "pesanPeringatan": None
    }
    if akun.tipeAkun == "TABUNGAN_OPERASIONAL" and akun.saldo < batasAman:
        data["statusDarurat"] = True
        data["pesanPeringatan"] = (
            f"Peringatan: Saldo operasional Rp{akun.saldo:,.0f} "
            f"di bawah batas aman Rp{batasAman:,.0f}."
        )
    return data


def ambilDaftarAkun(db: Session) -> List[dict]:
    batasAman = ambilBatasAmanCadangan(db)
    daftarAkun = db.query(AkunKeuangan).all()
    return [pasangStatusPeringatan(akun, batasAman) for akun in daftarAkun]


def ambilAkunBerdasarkanId(db: Session, idAkun: int) -> AkunKeuangan:
    akun = db.query(AkunKeuangan).filter(AkunKeuangan.id == idAkun).first()
    if not akun:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Akun dengan id {idAkun} tidak ditemukan"
        )
    return akun


def buatAkunBaru(db: Session, payload: AkunBuatSkema) -> dict:
    validasiTipeAkun(payload.tipeAkun)
    batasAman = ambilBatasAmanCadangan(db)
    saldoNominal = float(payload.saldo)
    akunBaru = AkunKeuangan(
        namaAkun=payload.namaAkun,
        namaBank=payload.namaBank,
        nomorRekening=payload.nomorRekening,
        tipeAkun=payload.tipeAkun,
        saldo=saldoNominal,
        terkunci=payload.terkunci
    )
    db.add(akunBaru)
    db.commit()
    db.refresh(akunBaru)

    # Catat mutasi saldo awal jika ada nominal > 0
    if saldoNominal > 0:
        db.add(TransaksiKeuangan(
            tanggal=datetime.utcnow(),
            tipeTransaksi="PEMASUKAN",
            kategori="Saldo Awal Rekening",
            sumberDana="Pendaftaran Akun",
            tujuanDana=akunBaru.namaAkun,
            nominal=saldoNominal,
            catatan=f"Saldo awal pembukaan rekening {akunBaru.namaAkun}"
        ))
        db.commit()

    return pasangStatusPeringatan(akunBaru, batasAman)


def perbaruiAkun(db: Session, idAkun: int, payload: AkunUbahSkema) -> dict:
    akun = ambilAkunBerdasarkanId(db, idAkun)
    batasAman = ambilBatasAmanCadangan(db)
    saldoLama = akun.saldo

    if payload.tipeAkun is not None:
        validasiTipeAkun(payload.tipeAkun)
        akun.tipeAkun = payload.tipeAkun

    if payload.namaAkun is not None:
        akun.namaAkun = payload.namaAkun
    if payload.namaBank is not None:
        akun.namaBank = payload.namaBank
    if payload.nomorRekening is not None:
        akun.nomorRekening = payload.nomorRekening

    if payload.saldo is not None:
        saldoBaru = float(payload.saldo)
        selisih = saldoBaru - saldoLama
        if abs(selisih) > 0.01:
            tipeMutasi = "PEMASUKAN" if selisih > 0 else "PENGELUARAN"
            catatanKoreksi = (
                f"Koreksi saldo {akun.namaAkun}: {'+' if selisih > 0 else ''}{selisih:,.0f} "
                f"(Sebelumnya: Rp{saldoLama:,.0f})"
            )
            db.add(TransaksiKeuangan(
                tanggal=datetime.utcnow(),
                tipeTransaksi=tipeMutasi,
                kategori="Penyesuaian Saldo Rekening",
                sumberDana="Koreksi Manual" if selisih > 0 else akun.namaAkun,
                tujuanDana=akun.namaAkun if selisih > 0 else "Koreksi Manual",
                nominal=abs(selisih),
                catatan=catatanKoreksi
            ))
        akun.saldo = saldoBaru

    if payload.terkunci is not None:
        akun.terkunci = payload.terkunci

    db.commit()
    db.refresh(akun)
    return pasangStatusPeringatan(akun, batasAman)


def hapusAkun(db: Session, idAkun: int) -> dict:
    akun = ambilAkunBerdasarkanId(db, idAkun)
    db.delete(akun)
    db.commit()
    return {"status": "sukses", "pesan": f"Akun {idAkun} berhasil dihapus"}
