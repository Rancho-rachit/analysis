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
    model_name: str = "gemini-1.5-flash"

@dataclass
class GeckoTerminalConfig:
    base_url: str = "https://api.geckoterminal.com/api/v2"

@dataclass
class Config:
    db: DatabaseConfig
    gemini: GeminiConfig
    gecko_terminal: GeckoTerminalConfig

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
            ),
            gecko_terminal=GeckoTerminalConfig(
                base_url=os.getenv('GECKO_TERMINAL_API_URL', 'https://api.geckoterminal.com/api/v2')
            )
        ) 