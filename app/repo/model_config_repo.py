import json
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from app.models.model_config.model_config import ModelConfig

_DEFAULT_MODEL_CONFIGS_PATH = "./data/model_configs.json"


def _file() -> Path:
    return Path(_DEFAULT_MODEL_CONFIGS_PATH)


def _read_all() -> dict:
    path = _file()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception as e:
        logger.error(f"Failed to read model configs file: {e}")
        return {}


def _write_all(data: dict) -> None:
    path = _file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


class ModelConfigRepo:

    def create(self, model_config: ModelConfig) -> ModelConfig:
        data = _read_all()
        data[model_config.model_id] = model_config.model_dump(mode="json")
        _write_all(data)
        return model_config

    def get(self, model_id: str) -> ModelConfig | None:
        data = _read_all()
        entry = data.get(model_id)
        if entry is None:
            return None
        return ModelConfig(**entry)

    def get_all(self) -> list[ModelConfig]:
        data = _read_all()
        return [ModelConfig(**v) for v in data.values()]

    def update(self, model_config: ModelConfig) -> ModelConfig:
        data = _read_all()
        if model_config.model_id not in data:
            logger.warning(f"update called for unknown model_id {model_config.model_id}")
            return model_config
        model_config.updated_at = datetime.now(timezone.utc).isoformat()
        data[model_config.model_id] = model_config.model_dump(mode="json")
        _write_all(data)
        return model_config

    def delete(self, model_id: str) -> bool:
        data = _read_all()
        if model_id not in data:
            return False
        del data[model_id]
        _write_all(data)
        return True
