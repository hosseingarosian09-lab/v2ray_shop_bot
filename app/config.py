from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_setup_code: str
    database_path: Path


def get_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is missing. Run setup.bat first.")

    setup_code = os.getenv("ADMIN_SETUP_CODE", "").strip()
    db_value = os.getenv("DATABASE_PATH", "data/bot.db").strip() or "data/bot.db"
    db_path = Path(db_value)
    if not db_path.is_absolute():
        db_path = BASE_DIR / db_path

    return Settings(
        bot_token=token,
        admin_setup_code=setup_code,
        database_path=db_path,
    )
