from enum import Enum

from pydantic import BaseModel


class PipelineMode(str, Enum):
    SEQUENTIAL = "sequential"
    ROUTER = "router"


class Pipeline(BaseModel):
    pipeline_id: str
    name: str
    mode: PipelineMode
    agent_ids: list[str] = []
    entry_agent_id: str | None = None
    created_at: str
    updated_at: str


class CreatePipelineRequest(BaseModel):
    name: str
    mode: PipelineMode
    agent_ids: list[str] = []
    entry_agent_id: str | None = None


class UpdatePipelineRequest(BaseModel):
    name: str | None = None
    mode: PipelineMode | None = None
    entry_agent_id: str | None = None


class PipelineStepResult(BaseModel):
    agent_id: str
    agent_name: str
    input: str
    output: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    rag_chunks_used: int


class PipelineRunRequest(BaseModel):
    message: str
    k: int = 5
    similarity_threshold: float = 0.7


class PipelineRunResponse(BaseModel):
    pipeline_id: str
    pipeline_name: str
    mode: PipelineMode
    steps: list[PipelineStepResult]
    final_response: str
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
