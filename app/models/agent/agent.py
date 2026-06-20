from enum import Enum

from pydantic import BaseModel


class AgentStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"


class Agent(BaseModel):
    agent_id: str
    name: str
    system_prompt: str
    status: AgentStatus = AgentStatus.DISABLED
    media_ids: list[str] = []
    tool_ids: list[str] = []
    llm_provider: str = "groq"
    model_id: str | None = None
    backup_model_id: str | None = None
    created_at: str
    updated_at: str


class CreateAgentRequest(BaseModel):
    name: str
    system_prompt: str
    media_ids: list[str] = []
    llm_provider: str = "groq"


class UpdateAgentRequest(BaseModel):
    name: str | None = None
    system_prompt: str | None = None
    llm_provider: str | None = None


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class AttachModelRequest(BaseModel):
    backup_model_id: str | None = None


class AgentChatRequest(BaseModel):
    message: str
    k: int = 5
    similarity_threshold: float = 0.7


class AgentChatResponse(BaseModel):
    agent_id: str
    agent_name: str
    message: str
    response: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    rag_chunks_used: int
