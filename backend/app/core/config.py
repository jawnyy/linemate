from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # --- Data files ---
    documents_csv_path: Path = BASE_DIR / "documents.csv"
    tickets_csv_path: Path = BASE_DIR / "tickets.csv"
    crew_csv_path: Path = BASE_DIR / "crew.csv"

    # --- API Key ---
    api_key: str = "dev-local-key"

    # --- Analytics ---
    staleness_threshold_days: int = 90

    # --- LLM / embeddings ---
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.2"
    embedding_model: str = "nomic-embed-text"

    # --- Vector store ---
    chroma_persist_dir: Path = BASE_DIR / "chroma_db"
    chunk_size: int = 500
    chunk_overlap: int = 50

    class Config:
        env_file = ".env"

settings = Settings()