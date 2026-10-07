import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"

# Pastikan folder database selalu tersedia
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = INSTANCE_DIR / "ganas_forms.db"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "ganas-dev-secret")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{DATABASE_PATH.as_posix()}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024