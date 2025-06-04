from dataclasses import dataclass
from typing import Optional
import os
import dotenv

dotenv.load_dotenv()

@dataclass
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str

@dataclass
class GeminiConfig:
    api_key: str
    model_name: str = "gemini-2.0-flash"

@dataclass
class Config:
    db: DatabaseConfig
    gemini: GeminiConfig

    @classmethod
    def from_env(cls) -> 'Config':
        return cls(
            db=DatabaseConfig(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '3306')),
                user=os.getenv('DB_USER', 'root'),
                password=os.getenv('DB_PASSWORD', ''),
                database=os.getenv('DB_NAME', 'analysis')
            ),
            gemini=GeminiConfig(
                api_key=os.getenv('GEMINI_API_KEY', '')
            )
        ) 