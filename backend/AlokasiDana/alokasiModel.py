from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AlokasiBuatSkema(BaseModel):
    idRekeningTujuan: str = Field(..., description="ID rekening bank/e-wallet penerima atau SAKU_TUNAI untuk Dompet Fisik")
    nominal: float = Field(..., gt=0, description="Nominal pemasukan uang yang masuk")
    kategori: str = Field(default="Gaji / Kiriman", min_length=1)
    catatan: Optional[str] = None


class AlokasiResponSkema(BaseModel):
    id: int
    tanggal: datetime
    totalPemasukan: float
    idRekeningTujuan: Optional[str] = None
    namaRekeningTujuan: Optional[str] = None
    catatan: Optional[str] = None

    class Config:
        from_attributes = True
