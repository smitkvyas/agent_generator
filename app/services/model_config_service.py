import uuid
from datetime import datetime, timezone

from app.models.model_config.model_config import (
    CreateModelConfigRequest,
    ModelConfig,
    UpdateModelConfigRequest,
)
from app.repo.model_config_repo import ModelConfigRepo


class ModelConfigService:

    def __init__(self):
        self._repo = ModelConfigRepo()

    def create(self, request: CreateModelConfigRequest) -> ModelConfig:
        now = datetime.now(timezone.utc).isoformat()
        model_config = ModelConfig(
            model_id=str(uuid.uuid4()),
            name=request.name,
            model_name=request.model_name,
            provider=request.provider,
            task=request.task,
            description=request.description,
            created_at=now,
            updated_at=now,
        )
        return self._repo.create(model_config)

    def get(self, model_id: str) -> ModelConfig | None:
        return self._repo.get(model_id)

    def get_all(self) -> list[ModelConfig]:
        return self._repo.get_all()

    def update(self, model_id: str, request: UpdateModelConfigRequest) -> ModelConfig | None:
        model_config = self._repo.get(model_id)
        if model_config is None:
            return None
        if request.name is not None:
            model_config.name = request.name
        if request.model_name is not None:
            model_config.model_name = request.model_name
        if request.provider is not None:
            model_config.provider = request.provider
        if request.task is not None:
            model_config.task = request.task
        if request.description is not None:
            model_config.description = request.description
        return self._repo.update(model_config)

    def delete(self, model_id: str) -> bool:
        return self._repo.delete(model_id)
