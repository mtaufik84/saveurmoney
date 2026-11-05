"""
Logika bisnis pencatatan alokasi pemasukan dana ke satu rekening riil atau dompet fisik.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.BasisData.skemaTabel import (
    AkunKeuangan,
    SakuTunai,
    TransaksiKeuangan,
    AlokasiRiwayat
)
from .alokasiModel import AlokasiBuatSkema


def prosesAlokasiDana(db: Session, payload: AlokasiBuatSkema) -> dict:
    """
    Mencatat pemasukan masuk langsung ke SATU pos tujuan:
    - Rekening bank / e-wallet riil (berdasarkan id)
    - Dompet Fisik Tunai (jika idRekeningTujuan == 'SAKU_TUNAI')
    """
    target = str(payload.idRekeningTujuan).strip()
    nominal = float(payload.nominal)
    waktuSekarang = datetime.utcnow()

    namaTujuan = ""
    idRekTujuan = target
    saldoBaru = 0.0

    if target == "SAKU_TUNAI":
        saku = db.query(SakuTunai).first()
        if not saku:
            saku = SakuTunai(saldoTunai=0.0, durasiHariKos=7)
            db.add(saku)
            db.flush()
        saku.saldoTunai += nominal
        namaTujuan = "Dompet Fisik (Tunai)"
        saldoBaru = saku.saldoTunai
    else:
        idInt = int(target) if target.isdigit() else None
        akun = None
        if idInt is not None:
            akun = db.query(AkunKeuangan).filter(AkunKeuangan.id == idInt).first()
        else:
            akun = db.query(AkunKeuangan).filter(AkunKeuangan.namaAkun == target).first()

        if not akun:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rekening tujuan '{target}' tidak ditemukan."
            )

        akun.saldo += nominal
        namaTujuan = akun.namaAkun
        saldoBaru = akun.saldo

    deskripsi = payload.catatan or f"Suntikan dana ke {namaTujuan}"

    # Catat mutasi transaksi
    transaksi = TransaksiKeuangan(
        tanggal=waktuSekarang,
        tipeTransaksi="PEMASUKAN",
        kategori=payload.kategori,
        sumberDana="Pemasukan Luar",
        tujuanDana=namaTujuan,
        nominal=nominal,
        catatan=deskripsi
    )
    db.add(transaksi)

    # Catat riwayat alokasi
    catatanRiwayat = AlokasiRiwayat(
        tanggal=waktuSekarang,
        totalPemasukan=nominal,
        idRekeningTujuan=int(target) if target.isdigit() else None,
        namaRekeningTujuan=namaTujuan,
        catatan=deskripsi
    )
    db.add(catatanRiwayat)

    db.commit()
    db.refresh(catatanRiwayat)

    return {
        "status": "sukses",
        "pesan": f"Pemasukan Rp{nominal:,.0f} berhasil masuk ke {namaTujuan}",
        "data": {
            "idAlokasi": catatanRiwayat.id,
            "tanggal": catatanRiwayat.tanggal.isoformat(),
            "totalPemasukan": catatanRiwayat.totalPemasukan,
            "idRekeningTujuan": target,
            "namaRekeningTujuan": namaTujuan,
            "saldoBaru": saldoBaru
        }
    }
