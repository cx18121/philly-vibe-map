"""Backend configuration via environment variables with sensible defaults."""
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    artifacts_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get("ARTIFACTS_DIR", "data/output/artifacts")
        )
    )
    host: str = field(
        default_factory=lambda: os.environ.get("HOST", "0.0.0.0")
    )
    port: int = field(
        default_factory=lambda: int(os.environ.get("PORT", "8080"))
    )


settings = Settings()
