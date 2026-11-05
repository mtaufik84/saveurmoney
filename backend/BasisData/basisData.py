"""
Modul konfigurasi basis data SQLite / Cloud Database dan sesi SQLAlchemy.
Mendukung Vercel Serverless (/tmp directory fallback & DATABASE_URL).
"""
import os
import shutil
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

URL_ENV = os.getenv("DATABASE_URL")

if URL_ENV:
    # Jika menggunakan PostgreSQL (misal Supabase, Neon, Neon Postgres di Vercel)
    if URL_ENV.startswith("postgres://"):
        URL_ENV = URL_ENV.replace("postgres://", "postgresql://", 1)
    URL_BASIS_DATA = URL_ENV
    mesinBasisData = create_engine(URL_BASIS_DATA)
else:
    # Lingkungan Vercel Serverless memiliki sistem filesystem read-only kecuali folder /tmp
    is_vercel = os.getenv("VERCEL") == "1" or os.getenv("VERCEL_ENV") is not None
    
    if is_vercel:
        direktoriBasisData = Path("/tmp")
        lokasiBasisData = direktoriBasisData / "app.db"
        # Jika database lokal ada di bundle repository, salin ke /tmp
        lokasiAsal = Path(__file__).resolve().parent.parent / "database" / "app.db"
        if lokasiAsal.exists() and not lokasiBasisData.exists():
            shutil.copyfile(lokasiAsal, lokasiBasisData)
    else:
        direktoriBasisData = Path(__file__).resolve().parent.parent / "database"
        direktoriBasisData.mkdir(parents=True, exist_ok=True)
        lokasiBasisData = direktoriBasisData / "app.db"

    URL_BASIS_DATA = f"sqlite:///{lokasiBasisData.as_posix()}"
    mesinBasisData = create_engine(
        URL_BASIS_DATA,
        connect_args={"check_same_thread": False}
    )

SesiLokal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=mesinBasisData
)

BasisTabel = declarative_base()


def ambilSesiBasisData():
    """
    Generator dependency untuk sesi basis data per request.
    """
    sesi = SesiLokal()
    try:
        yield sesi
    finally:
        sesi.close()
