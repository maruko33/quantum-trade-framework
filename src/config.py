import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def must_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env: {name}")
    return v.strip()


@dataclass(frozen=True)
class Settings:
    trading_mode: str
    ib_host: str
    ib_port: int
    ib_client_id: int


def get_settings() -> Settings:
    trading_mode = os.getenv("TRADING_MODE", "PAPER").strip().upper()
    ib_host = os.getenv("IB_HOST", "127.0.0.1").strip()
    ib_port = int(os.getenv("IB_PORT", "7497").strip())
    ib_client_id = int(os.getenv("IB_CLIENT_ID", "7").strip())
    return Settings(
        trading_mode=trading_mode,
        ib_host=ib_host,
        ib_port=ib_port,
        ib_client_id=ib_client_id,
    )
