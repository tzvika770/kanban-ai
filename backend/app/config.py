import os
import warnings
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# Load .env from the nearest location walking up from the CWD. In Docker the
# vars are injected via docker-compose env_file, so a missing file is fine.
load_dotenv(find_dotenv(usecwd=True))

_DEFAULT_SECRET = "dev-secret-key-change-in-production"
SECRET_KEY = os.getenv("SECRET_KEY") or _DEFAULT_SECRET
if not os.getenv("SECRET_KEY"):
    warnings.warn(
        "SECRET_KEY is not set; using an insecure default. Set SECRET_KEY in .env "
        "before deploying beyond local development.",
        stacklevel=2,
    )

# Database location: honor DATABASE_URL if set, else a SQLite file under data/.
_DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "app.db"
DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{_DEFAULT_DB_PATH}"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b")
