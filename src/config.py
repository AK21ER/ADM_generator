from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    model: str
    discount_rate: float
    project_root: Path

def get_settings(project_root: Path) -> Settings:
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        model=os.getenv("OPENAI_MODEL", "gpt-4.1").strip(),
        discount_rate=float(os.getenv("DISCOUNT_RATE", "0.10")),
        project_root=project_root,
    )
