import os

from dotenv import find_dotenv, load_dotenv

# Load .env from the nearest location walking up from the CWD. In Docker the
# vars are injected via docker-compose env_file, so a missing file is fine.
load_dotenv(find_dotenv(usecwd=True))

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b")
