import os
from pathlib import Path

from dotenv import load_dotenv


def load_environment() -> None:
    """
    Load environment variables by profile.
    - development (default): .env
    - production: .env.production
    """
    root_dir = Path(__file__).resolve().parents[1]
    environment = os.getenv("ENVIRONMENT", "development").strip().lower()
    env_filename = ".env.production" if environment == "production" else ".env"
    env_path = root_dir / env_filename

    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
    else:
        load_dotenv(override=False)
