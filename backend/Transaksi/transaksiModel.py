"""
Skema data Pydantic untuk modul Transaksi, Target, dan Pengaturan.
"""
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field


class TransaksiBuatSkema(BaseModel):
    tipeTransaksi: str = Field(default="PENGELUARAN", description="PENGELUARAN, PEMASUKAN, PINDAH_DANA, PENYESUAIAN_KAS")
    kategori: str = Field(default="Umum", min_length=1)
    sumberDana: str = Field(..., description="Nama akun, id akun, SAKU_TUNAI, atau TABUNGAN_OPERASIONAL")
    tujuanDana: Optional[str] = None
    nominal: float = Field(..., gt=0)
    catatan: Optional[str] = None


class TransaksiResponSkema(BaseModel):
    id: int
    tanggal: datetime
    tipeTransaksi: str
    kategori: str
    sumberDana: str
    tujuanDana: Optional[str] = None
    nominal: float
    catatan: Optional[str] = None

    class Config:
        from_attributes = True


class PindahDanaSkema(BaseModel):
    idDari: int = Field(..., description="ID rekening sumber")
    idTujuan: int = Field(..., description="ID rekening penerima")
    nominal: float = Field(..., gt=0)
    catatan: Optional[str] = None


class SakuTunaiUbahSkema(BaseModel):
    saldoTunai: Optional[float] = Field(default=None, ge=0)
    durasiHariKos: Optional[int] = Field(default=None, ge=1)
    alasan: Optional[str] = Field(default=None, description="Keterangan koreksi fisik")


class SakuTunaiResponSkema(BaseModel):
    id: int
    saldoTunai: float
    durasiHariKos: int
    batasMakanHarian: float

    class Config:
        from_attributes = True


class TargetTabunganBuatSkema(BaseModel):
    namaTarget: str = Field(..., min_length=1, max_length=150)
    nominalSasaran: float = Field(..., gt=0)
    tenggatWaktu: date
    idAkunTerhubung: Optional[int] = None


class TargetTabunganUbahSkema(BaseModel):
    namaTarget: Optional[str] = None
    nominalSasaran: Optional[float] = None
    tenggatWaktu: Optional[date] = None
    idAkunTerhubung: Optional[int] = None


class TargetTabunganResponSkema(BaseModel):
    id: int
    namaTarget: str
    nominalSasaran: float
    tenggatWaktu: date
    idAkunTerhubung: Optional[int] = None
    totalTerkumpul: float = 0.0
    sisaKekurangan: float = 0.0
    sisaHari: int = 0
    sisaSiklus: int = 1
    wajibSimpanPerSiklus: float = 0.0

    class Config:
        from_attributes = True


class PengaturanBatasAmanSkema(BaseModel):
    batasAmanCadangan: float = Field(..., ge=0, description="Nominal batas aman kas operasional")
