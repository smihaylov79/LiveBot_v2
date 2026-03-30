from pathlib import Path
import yaml


class LiveConfigLoader:
    def __init__(self, path: str = "config/live_settings.yaml"):
        self.path = Path(path)

    def load(self) -> dict:
        with self.path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)
