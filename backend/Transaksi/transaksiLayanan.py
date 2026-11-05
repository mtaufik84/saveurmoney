"""
Logika bisnis transaksi, saku tunai, pindah dana, target tabungan, dan seed data.
"""
import math
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.BasisData.skemaTabel import (
    AkunKeuangan,
    SakuTunai,
    TransaksiKeuangan,
    TargetTabungan,
    AlokasiRiwayat,
    PengaturanAplikasi
)
from backend.KelolaAkun.akunLayanan import ambilBatasAmanCadangan
from .transaksiModel import (
    TransaksiBuatSkema,
    PindahDanaSkema,
    SakuTunaiUbahSkema,
    TargetTabunganBuatSkema,
    TargetTabunganUbahSkema
)


# ==========================================
# 1. SAKU TUNAI & BATAS AMAN MAKAN
# ==========================================

def ambilAtauBuatSakuTunai(db: Session) -> SakuTunai:
    saku = db.query(SakuTunai).first()
    if not saku:
        saku = SakuTunai(saldoTunai=0.0, durasiHariKos=7)
        db.add(saku)
        db.commit()
        db.refresh(saku)
    return saku


def hitungBatasMakanHarian(saldoTunai: float, durasiHari: int) -> float:
    sisaHari = max(1, durasiHari)
    return float(math.floor(saldoTunai / sisaHari))


def perbaruiSakuTunai(db: Session, payload: SakuTunaiUbahSkema) -> dict:
    saku = ambilAtauBuatSakuTunai(db)
    saldoLama = saku.saldoTunai

    if payload.durasiHariKos is not None:
        saku.durasiHariKos = payload.durasiHariKos

    if payload.saldoTunai is not None:
        saldoBaru = float(payload.saldoTunai)
        selisih = saldoBaru - saldoLama

        if abs(selisih) > 0.01:
            tipe = "PENYESUAIAN_KAS"
            alasanKustom = f" - {payload.alasan}" if payload.alasan else ""
            catatan = (
                f"Koreksi fisik dompet: {'+' if selisih > 0 else ''}{selisih:,.0f} "
                f"(Sebelumnya: Rp{saldoLama:,.0f}){alasanKustom}"
            )
            transaksiKoreksi = TransaksiKeuangan(
                tanggal=datetime.utcnow(),
                tipeTransaksi=tipe,
                kategori="Penyesuaian Saku Tunai",
                sumberDana="SAKU_TUNAI",
                tujuanDana="Dompet Fisik",
                nominal=abs(selisih),
                catatan=catatan
            )
            db.add(transaksiKoreksi)

        saku.saldoTunai = saldoBaru

    db.commit()
    db.refresh(saku)

    return {
        "id": saku.id,
        "saldoTunai": saku.saldoTunai,
        "durasiHariKos": saku.durasiHariKos,
        "batasMakanHarian": hitungBatasMakanHarian(saku.saldoTunai, saku.durasiHariKos)
    }


# ==========================================
# 2. CATAT TRANSAKSI BELANJA & MUTASI
# ==========================================

def catatTransaksi(db: Session, payload: TransaksiBuatSkema) -> TransaksiKeuangan:
    sumber = payload.sumberDana.strip()
    nominal = float(payload.nominal)
    waktuSekarang = datetime.utcnow()

    if payload.tipeTransaksi == "PENGELUARAN":
        if sumber == "SAKU_TUNAI":
            saku = ambilAtauBuatSakuTunai(db)
            if saku.saldoTunai < nominal:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Saldo Saku Tunai (Rp{saku.saldoTunai:,.0f}) tidak cukup untuk pengeluaran Rp{nominal:,.0f}."
                )
            saku.saldoTunai -= nominal
        else:
            akun = None
            if sumber.isdigit():
                akun = db.query(AkunKeuangan).filter(AkunKeuangan.id == int(sumber)).first()
            elif sumber == "TABUNGAN_OPERASIONAL":
                akun = db.query(AkunKeuangan).filter(AkunKeuangan.tipeAkun == "TABUNGAN_OPERASIONAL").first()
            elif sumber == "TABUNGAN_UTAMA":
                akun = db.query(AkunKeuangan).filter(AkunKeuangan.tipeAkun == "TABUNGAN_UTAMA").first()
            else:
                akun = db.query(AkunKeuangan).filter(AkunKeuangan.namaAkun == sumber).first()

            if not akun:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Sumber dana rekening '{sumber}' tidak ditemukan."
                )

            if akun.saldo < nominal:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Saldo akun {akun.namaAkun} (Rp{akun.saldo:,.0f}) tidak mencukupi untuk transaksi Rp{nominal:,.0f}."
                )

            akun.saldo -= nominal
            sumber = akun.namaAkun

    transaksi = TransaksiKeuangan(
        tanggal=waktuSekarang,
        tipeTransaksi=payload.tipeTransaksi,
        kategori=payload.kategori,
        sumberDana=sumber,
        tujuanDana=payload.tujuanDana,
        nominal=nominal,
        catatan=payload.catatan
    )

    db.add(transaksi)
    db.commit()
    db.refresh(transaksi)
    return transaksi


def ambilDaftarTransaksi(db: Session, limit: int = 100) -> List[TransaksiKeuangan]:
    return (
        db.query(TransaksiKeuangan)
        .order_by(TransaksiKeuangan.tanggal.desc())
        .limit(limit)
        .all()
    )


# ==========================================
# 3. PINDAH DANA ANTAR REKENING
# ==========================================

def prosesPindahDana(db: Session, payload: PindahDanaSkema) -> dict:
    if payload.idDari == payload.idTujuan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rekening sumber dan rekening penerima tidak boleh sama."
        )

    akunDari = db.query(AkunKeuangan).filter(AkunKeuangan.id == payload.idDari).first()
    akunTujuan = db.query(AkunKeuangan).filter(AkunKeuangan.id == payload.idTujuan).first()

    if not akunDari or not akunTujuan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Salah satu rekening transfer tidak ditemukan."
        )

    if akunDari.saldo < payload.nominal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Saldo {akunDari.namaAkun} (Rp{akunDari.saldo:,.0f}) tidak cukup untuk transfer Rp{payload.nominal:,.0f}."
        )

    akunDari.saldo -= payload.nominal
    akunTujuan.saldo += payload.nominal

    transaksi = TransaksiKeuangan(
        tanggal=datetime.utcnow(),
        tipeTransaksi="PINDAH_DANA",
        kategori="Transfer Rekening",
        sumberDana=akunDari.namaAkun,
        tujuanDana=akunTujuan.namaAkun,
        nominal=payload.nominal,
        catatan=payload.catatan or f"Pindah dana dari {akunDari.namaAkun} ke {akunTujuan.namaAkun}"
    )

    db.add(transaksi)
    db.commit()
    db.refresh(transaksi)

    return {
        "status": "sukses",
        "pesan": f"Berhasil memindahkan Rp{payload.nominal:,.0f} dari {akunDari.namaAkun} ke {akunTujuan.namaAkun}",
        "idTransaksi": transaksi.id
    }


# ==========================================
# 4. TARGET TABUNGAN DINAMIS
# ==========================================

def kalkulasiDetailTarget(target: TargetTabungan, totalSaldoUtama: float, durasiSiklusHari: int = 7) -> dict:
    hariSekarang = date.today()
    selisihHari = (target.tenggatWaktu - hariSekarang).days
    selisihHari = max(0, selisihHari)

    sisaKekurangan = max(0.0, target.nominalSasaran - totalSaldoUtama)
    sisaSiklus = max(1, math.ceil(selisihHari / max(1, durasiSiklusHari)))
    wajibSimpanPerSiklus = math.ceil(sisaKekurangan / sisaSiklus) if sisaKekurangan > 0 else 0.0

    return {
        "id": target.id,
        "namaTarget": target.namaTarget,
        "nominalSasaran": target.nominalSasaran,
        "tenggatWaktu": target.tenggatWaktu,
        "idAkunTerhubung": target.idAkunTerhubung,
        "totalTerkumpul": totalSaldoUtama,
        "sisaKekurangan": sisaKekurangan,
        "sisaHari": selisihHari,
        "sisaSiklus": sisaSiklus,
        "wajibSimpanPerSiklus": float(wajibSimpanPerSiklus)
    }


def ambilDaftarTarget(db: Session) -> List[dict]:
    daftarTarget = db.query(TargetTabungan).all()
    saku = ambilAtauBuatSakuTunai(db)
    durasiSiklus = saku.durasiHariKos

    akunUtamaList = db.query(AkunKeuangan).filter(AkunKeuangan.tipeAkun == "TABUNGAN_UTAMA").all()
    totalSaldoUtama = sum(a.saldo for a in akunUtamaList)

    hasil = []
    for t in daftarTarget:
        saldoAkunTerkait = totalSaldoUtama
        if t.idAkunTerhubung:
            akunTerkait = db.query(AkunKeuangan).filter(AkunKeuangan.id == t.idAkunTerhubung).first()
            if akunTerkait:
                saldoAkunTerkait = akunTerkait.saldo
        hasil.append(kalkulasiDetailTarget(t, saldoAkunTerkait, durasiSiklus))
    return hasil


def buatTargetTabungan(db: Session, payload: TargetTabunganBuatSkema) -> dict:
    targetBaru = TargetTabungan(
        namaTarget=payload.namaTarget,
        nominalSasaran=float(payload.nominalSasaran),
        tenggatWaktu=payload.tenggatWaktu,
        idAkunTerhubung=payload.idAkunTerhubung
    )
    db.add(targetBaru)
    db.commit()
    db.refresh(targetBaru)

    saku = ambilAtauBuatSakuTunai(db)
    akunUtama = db.query(AkunKeuangan).filter(AkunKeuangan.tipeAkun == "TABUNGAN_UTAMA").first()
    saldoAwal = akunUtama.saldo if akunUtama else 0.0
    return kalkulasiDetailTarget(targetBaru, saldoAwal, saku.durasiHariKos)


def perbaruiTargetTabungan(db: Session, idTarget: int, payload: TargetTabunganUbahSkema) -> dict:
    target = db.query(TargetTabungan).filter(TargetTabungan.id == idTarget).first()
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target tabungan dengan id {idTarget} tidak ditemukan."
        )

    if payload.namaTarget is not None:
        target.namaTarget = payload.namaTarget
    if payload.nominalSasaran is not None:
        target.nominalSasaran = float(payload.nominalSasaran)
    if payload.tenggatWaktu is not None:
        target.tenggatWaktu = payload.tenggatWaktu
    if payload.idAkunTerhubung is not None:
        target.idAkunTerhubung = payload.idAkunTerhubung

    db.commit()
    db.refresh(target)

    saku = ambilAtauBuatSakuTunai(db)
    saldoAkun = 0.0
    if target.idAkunTerhubung:
        a = db.query(AkunKeuangan).filter(AkunKeuangan.id == target.idAkunTerhubung).first()
        saldoAkun = a.saldo if a else 0.0
    else:
        utama = db.query(AkunKeuangan).filter(AkunKeuangan.tipeAkun == "TABUNGAN_UTAMA").first()
        saldoAkun = utama.saldo if utama else 0.0

    return kalkulasiDetailTarget(target, saldoAkun, saku.durasiHariKos)


# ==========================================
# 5. RINGKASAN KPI DASBOR
# ==========================================

def ambilRingkasanKPI(db: Session) -> dict:
    saku = ambilAtauBuatSakuTunai(db)
    akunList = db.query(AkunKeuangan).all()
    batasAman = ambilBatasAmanCadangan(db)

    totalKasOperasional = sum(a.saldo for a in akunList if a.tipeAkun == "TABUNGAN_OPERASIONAL")
    totalTabunganUtama = sum(a.saldo for a in akunList if a.tipeAkun == "TABUNGAN_UTAMA")
    batasMakanHariIni = hitungBatasMakanHarian(saku.saldoTunai, saku.durasiHariKos)

    statusDarurat = any(
        a.tipeAkun == "TABUNGAN_OPERASIONAL" and a.saldo < batasAman
        for a in akunList
    )

    return {
        "batasMakanHariIni": batasMakanHariIni,
        "saldoSakuTunai": saku.saldoTunai,
        "sisaHariKos": saku.durasiHariKos,
        "totalKasOperasional": totalKasOperasional,
        "totalTabunganUtama": totalTabunganUtama,
        "batasAmanCadangan": batasAman,
        "statusDarurat": statusDarurat,
        "pesanDarurat": (
            f"Kas operasional berada di bawah batas aman (Rp{batasAman:,.0f})."
            if statusDarurat else "Kondisi kas aman dan terkendali."
        )
    }


# ==========================================
# 6. SEED DATA AWAL & RESET DATA
# ==========================================

def inisialisasiSeedAwal(db: Session) -> None:
    # 1. Pastikan setting batas aman ada
    pengaturan = db.query(PengaturanAplikasi).filter(
        PengaturanAplikasi.kunci == "batasAmanCadangan"
    ).first()
    if not pengaturan:
        db.add(PengaturanAplikasi(kunci="batasAmanCadangan", nilai="200000"))

    # 2. Akun default
    jumlahAkun = db.query(AkunKeuangan).count()
    if jumlahAkun == 0:
        akunUtama = AkunKeuangan(
            namaAkun="Bank BCA Dingin",
            namaBank="BCA",
            nomorRekening="8801928374",
            tipeAkun="TABUNGAN_UTAMA",
            saldo=739624.0,
            terkunci=True
        )
        akunOperasional = AkunKeuangan(
            namaAkun="Bank Mandiri Harian",
            namaBank="Mandiri",
            nomorRekening="1320098765432",
            tipeAkun="TABUNGAN_OPERASIONAL",
            saldo=242000.0,
            terkunci=False
        )
        db.add(akunUtama)
        db.add(akunOperasional)

    saku = db.query(SakuTunai).first()
    if not saku:
        saku = SakuTunai(
            saldoTunai=140000.0,
            durasiHariKos=7
        )
        db.add(saku)
    elif saku.saldoTunai == 0.0 and jumlahAkun == 0:
        saku.saldoTunai = 140000.0
        saku.durasiHariKos = 7

    db.commit()


def resetDataDatabase(db: Session) -> dict:
    """
    Hapus semua transaksi, riwayat alokasi, target, dan kembalikan akun serta saku ke seed awal.
    """
    db.query(TransaksiKeuangan).delete()
    db.query(AlokasiRiwayat).delete()
    db.query(TargetTabungan).delete()
    db.query(AkunKeuangan).delete()
    db.query(SakuTunai).delete()
    db.query(PengaturanAplikasi).delete()
    db.commit()

    inisialisasiSeedAwal(db)

    return {
        "status": "sukses",
        "pesan": "Basis data berhasil direset ke status seed awal v3.0"
    }
