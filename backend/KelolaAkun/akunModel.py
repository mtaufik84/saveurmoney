"""
Skema data Pydantic untuk modul KelolaAkun.
"""
from typing import Optional
from pydantic import BaseModel, Field


class AkunBuatSkema(BaseModel):
    namaAkun: str = Field(..., min_length=1, max_length=100)
    namaBank: str = Field(..., min_length=1, max_length=50)
    nomorRekening: Optional[str] = None
    tipeAkun: str = Field(..., description="TABUNGAN_UTAMA atau TABUNGAN_OPERASIONAL")
    saldo: float = Field(default=0.0, ge=0)
    terkunci: bool = Field(default=False)


class AkunUbahSkema(BaseModel):
    namaAkun: Optional[str] = None
    namaBank: Optional[str] = None
    nomorRekening: Optional[str] = None
    tipeAkun: Optional[str] = None
    saldo: Optional[float] = None
    terkunci: Optional[bool] = None


class AkunResponSkema(BaseModel):
    id: int
    namaAkun: str
    namaBank: str
    nomorRekening: Optional[str] = None
    tipeAkun: str
    saldo: float
    terkunci: bool
    statusDarurat: bool = False
    pesanPeringatan: Optional[str] = None

    class Config:
        from_attributes = True
