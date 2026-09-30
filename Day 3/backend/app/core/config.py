import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GROK_API_KEY: str
    GROK_BASE_URL: str = "https://api.x.ai/v1"
    MODEL_NAME: str = "grok-2-1212"
    
    # Base directory for the backend (D:/Day 3/backend)
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    @property
    def UPLOAD_DIR(self) -> str:
        path = os.path.join(self.BASE_DIR, "uploads")
        os.makedirs(path, exist_ok=True)
        return path
        
    @property
    def VECTORSTORE_DIR(self) -> str:
        path = os.path.join(self.BASE_DIR, "vectorstore")
        os.makedirs(path, exist_ok=True)
        return path

    model_config = SettingsConfigDict(
        # Look for .env file at D:/Day 3/.env
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
