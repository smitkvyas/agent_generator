from fastapi import APIRouter, Depends, HTTPException

from app.models.model_config.model_config import (
    CreateModelConfigRequest,
    ModelConfig,
    UpdateModelConfigRequest,
)
from app.services.model_config_service import ModelConfigService

router = APIRouter(prefix="/models", tags=["models"])


def _get_model_or_404(model_id: str, service: ModelConfigService) -> ModelConfig:
    model_config = service.get(model_id)
    if model_config is None:
        raise HTTPException(status_code=404, detail=f"Model config {model_id!r} not found")
    return model_config


@router.post("", status_code=201)
def create_model_config(request: CreateModelConfigRequest, service: ModelConfigService = Depends()) -> ModelConfig:
    return service.create(request)


@router.get("")
def list_model_configs(service: ModelConfigService = Depends()) -> list[ModelConfig]:
    return service.get_all()


@router.get("/{model_id}")
def get_model_config(model_id: str, service: ModelConfigService = Depends()) -> ModelConfig:
    return _get_model_or_404(model_id, service)


@router.patch("/{model_id}")
def update_model_config(
    model_id: str, request: UpdateModelConfigRequest, service: ModelConfigService = Depends()
) -> ModelConfig:
    model_config = service.update(model_id, request)
    if model_config is None:
        raise HTTPException(status_code=404, detail=f"Model config {model_id!r} not found")
    return model_config


@router.delete("/{model_id}", status_code=204)
def delete_model_config(model_id: str, service: ModelConfigService = Depends()) -> None:
    if not service.delete(model_id):
        raise HTTPException(status_code=404, detail=f"Model config {model_id!r} not found")
