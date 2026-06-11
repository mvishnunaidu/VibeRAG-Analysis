import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load local .env if it exists
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# App Configuration
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8000"))
ENV = os.getenv("ENV", "development")

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Directory configurations
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CHROMA_DIR = DATA_DIR / "chromadb"

def validate_config():
    """Validates configuration on startup without hard crashes, alerting the user to missing keys."""
    if not OPENAI_API_KEY:
        print("[WARNING] OPENAI_API_KEY is not set in the environment or .env file.")
        print("[WARNING] The RAG Chatbot will require an OpenAI key to perform embeddings and chat analysis.")
        print("[WARNING] Please update your .env file or environment variables before using the chat.")
        return False
    return True
