"""
Model Pydantic dan Layanan Otentikasi Admin SAVETRACK.
"""
import hashlib
import hmac
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.BasisData import PenggunaAdmin

KUNCI_RAHASIA = "SAVETRACK-KUNCI-RAHASIA-SUPER-AMAN-2026"


class DaftarAdminSkema(BaseModel):
    namaLengkap: str = Field(..., min_length=2, max_length=100)
    namaPengguna: str = Field(..., min_length=3, max_length=50)
    kataSandi: str = Field(..., min_length=6, max_length=100)


class MasukAdminSkema(BaseModel):
    namaPengguna: str
    kataSandi: str


def hashKataSandi(kataSandi: str) -> str:
    """Melakukan hashing SHA-256 dengan salt rahasia."""
    return hmac.new(KUNCI_RAHASIA.encode('utf-8'), kataSandi.encode('utf-8'), hashlib.sha256).hexdigest()


def verifikasiKataSandi(kataSandi: str, kataSandiHash: str) -> bool:
    """Mencocokkan kata sandi input dengan hash tersimpan."""
    inputHash = hashKataSandi(kataSandi)
    return hmac.compare_digest(inputHash, kataSandiHash)


def cekApakahAdminSudahAda(db: Session) -> bool:
    """Mengecek apakah akun admin tunggal sudah pernah didaftarkan."""
    return db.query(PenggunaAdmin).first() is not None


def daftarkanAdminTunggal(db: Session, payload: DaftarAdminSkema) -> PenggunaAdmin:
    """Mendaftarkan akun admin pertama (hanya diizinkan sekali)."""
    if cekApakahAdminSudahAda(db):
        raise ValueError("Akun admin sudah terdaftar. Registrasi baru ditutup demi keamanan.")

    adminBaru = PenggunaAdmin(
        namaLengkap=payload.namaLengkap.strip(),
        namaPengguna=payload.namaPengguna.strip().lower(),
        kataSandiHash=hashKataSandi(payload.kataSandi),
        peran="ADMIN",
        dibuatPada=datetime.utcnow()
    )
    db.add(adminBaru)
    db.commit()
    db.refresh(adminBaru)
    return adminBaru


def otentikasiAdmin(db: Session, payload: MasukAdminSkema) -> Optional[PenggunaAdmin]:
    """Memverifikasi username dan kata sandi admin."""
    pengguna = db.query(PenggunaAdmin).filter(
        PenggunaAdmin.namaPengguna == payload.namaPengguna.strip().lower()
    ).first()

    if not pengguna:
        return None

    if not verifikasiKataSandi(payload.kataSandi, pengguna.kataSandiHash):
        return None

    return pengguna


def buatTokenSesi(idPengguna: int, namaPengguna: str) -> str:
    """Membuat tanda tangan sesi tamper-proof."""
    data = f"{idPengguna}:{namaPengguna}"
    ttd = hmac.new(KUNCI_RAHASIA.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{data}:{ttd}"


def verifikasiTokenSesi(token: Optional[str]) -> Optional[str]:
    """Mengembalikan nama pengguna jika token valid."""
    if not token or ":" not in token:
        return None
    bagian = token.split(":")
    if len(bagian) != 3:
        return None
    idStr, namaPengguna, ttd = bagian
    data = f"{idStr}:{namaPengguna}"
    ttdEkspektasi = hmac.new(KUNCI_RAHASIA.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()
    if hmac.compare_digest(ttd, ttdEkspektasi):
        return namaPengguna
    return None
