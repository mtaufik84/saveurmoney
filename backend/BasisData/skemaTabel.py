"""
Skema tabel basis data SQLAlchemy untuk SAVETRACK.
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship

from .basisData import BasisTabel


class PengaturanAplikasi(BasisTabel):
    __tablename__ = "pengaturan"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    kunci = Column(String(50), unique=True, nullable=False)
    nilai = Column(String(100), nullable=False)


class AkunKeuangan(BasisTabel):
    __tablename__ = "akun"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    namaAkun = Column(String(100), nullable=False)
    namaBank = Column(String(50), nullable=False)
    nomorRekening = Column(String(50), nullable=True)
    tipeAkun = Column(String(50), nullable=False)  # TABUNGAN_UTAMA atau TABUNGAN_OPERASIONAL
    saldo = Column(Float, default=0.0, nullable=False)
    terkunci = Column(Boolean, default=False, nullable=False)

    targetTerhubung = relationship("TargetTabungan", back_populates="akunTerhubung")


class TargetTabungan(BasisTabel):
    __tablename__ = "target_tabungan"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    namaTarget = Column(String(150), nullable=False)
    nominalSasaran = Column(Float, default=0.0, nullable=False)
    tenggatWaktu = Column(Date, nullable=False)
    idAkunTerhubung = Column(Integer, ForeignKey("akun.id"), nullable=True)

    akunTerhubung = relationship("AkunKeuangan", back_populates="targetTerhubung")


class SakuTunai(BasisTabel):
    __tablename__ = "saku_tunai"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    saldoTunai = Column(Float, default=0.0, nullable=False)
    durasiHariKos = Column(Integer, default=7, nullable=False)


class TransaksiKeuangan(BasisTabel):
    __tablename__ = "transaksi"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tanggal = Column(DateTime, default=datetime.utcnow, nullable=False)
    tipeTransaksi = Column(String(50), nullable=False)  # PENGELUARAN, PEMASUKAN, PINDAH_DANA, PENYESUAIAN_KAS
    kategori = Column(String(100), nullable=False)
    sumberDana = Column(String(100), nullable=False)
    tujuanDana = Column(String(100), nullable=True)
    nominal = Column(Float, nullable=False)
    catatan = Column(String(255), nullable=True)


class AlokasiRiwayat(BasisTabel):
    __tablename__ = "alokasi_riwayat"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tanggal = Column(DateTime, default=datetime.utcnow, nullable=False)
    totalPemasukan = Column(Float, nullable=False)
    idRekeningTujuan = Column(Integer, nullable=True)
    namaRekeningTujuan = Column(String(100), nullable=True)
    catatan = Column(String(255), nullable=True)


class PenggunaAdmin(BasisTabel):
    __tablename__ = "pengguna_admin"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    namaLengkap = Column(String(100), nullable=False)
    namaPengguna = Column(String(50), unique=True, index=True, nullable=False)
    kataSandiHash = Column(String(255), nullable=False)
    peran = Column(String(20), default="ADMIN", nullable=False)  # ADMIN
    dibuatPada = Column(DateTime, default=datetime.utcnow, nullable=False)
