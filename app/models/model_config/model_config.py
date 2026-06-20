from enum import Enum

from pydantic import BaseModel


class ModelProvider(str, Enum):
    GROQ = "groq"
    LOCAL_HF = "local_hf"


class ModelTask(str, Enum):
    CHAT = "chat"
    TEXT_GENERATION = "text_generation"
    EMBEDDING = "embedding"
    TAGGING = "tagging"


class ModelConfig(BaseModel):
    model_id: str
    name: str
    model_name: str
    provider: ModelProvider
    task: ModelTask
    description: str = ""
    created_at: str
    updated_at: str


class CreateModelConfigRequest(BaseModel):
    name: str
    model_name: str
    provider: ModelProvider
    task: ModelTask
    description: str = ""


class UpdateModelConfigRequest(BaseModel):
    name: str | None = None
    model_name: str | None = None
    provider: ModelProvider | None = None
    task: ModelTask | None = None
    description: str | None = None
