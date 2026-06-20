import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.models.agent.agent import Agent, AgentChatResponse, AttachModelRequest, CreateAgentRequest, UpdateAgentRequest
from app.services.agent_chat_service import AgentChatService
from app.services.agent_service import AgentService

router = APIRouter(prefix="/agents", tags=["agents"])


def _get_agent_or_404(agent_id: str, service: AgentService) -> Agent:
    agent = service.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    return agent


@router.post("", status_code=201)
def create_agent(request: CreateAgentRequest, service: AgentService = Depends()) -> Agent:
    return service.create(request)


@router.get("")
def list_agents(service: AgentService = Depends()) -> list[Agent]:
    return service.get_all()


@router.get("/{agent_id}")
def get_agent(agent_id: str, service: AgentService = Depends()) -> Agent:
    return _get_agent_or_404(agent_id, service)


@router.delete("/{agent_id}", status_code=204)
def delete_agent(agent_id: str, service: AgentService = Depends()) -> None:
    if not service.delete(agent_id):
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")


@router.patch("/{agent_id}")
def update_agent(agent_id: str, request: UpdateAgentRequest, service: AgentService = Depends()) -> Agent:
    agent = service.update(agent_id, request)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    return agent


@router.patch("/{agent_id}/enable")
def enable_agent(agent_id: str, service: AgentService = Depends()) -> Agent:
    agent = service.enable(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    return agent


@router.patch("/{agent_id}/disable")
def disable_agent(agent_id: str, service: AgentService = Depends()) -> Agent:
    agent = service.disable(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    return agent


@router.post("/{agent_id}/media/{media_id}")
def attach_media(agent_id: str, media_id: str, service: AgentService = Depends()) -> Agent:
    agent = service.attach_media(agent_id, media_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    return agent


@router.delete("/{agent_id}/media/{media_id}")
def detach_media(agent_id: str, media_id: str, service: AgentService = Depends()) -> Agent:
    agent = service.detach_media(agent_id, media_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    return agent


@router.post("/{agent_id}/tools/{tool_id}")
def attach_tool(agent_id: str, tool_id: str, service: AgentService = Depends()) -> Agent:
    agent = service.attach_tool(agent_id, tool_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    return agent


@router.delete("/{agent_id}/tools/{tool_id}")
def detach_tool(agent_id: str, tool_id: str, service: AgentService = Depends()) -> Agent:
    agent = service.detach_tool(agent_id, tool_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    return agent


@router.post("/{agent_id}/models/{model_id}")
def attach_model(
    agent_id: str,
    model_id: str,
    request: AttachModelRequest = AttachModelRequest(),
    service: AgentService = Depends(),
) -> Agent:
    agent = service.attach_model(agent_id, model_id, backup_model_id=request.backup_model_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    return agent


@router.delete("/{agent_id}/models")
def detach_model(agent_id: str, service: AgentService = Depends()) -> Agent:
    agent = service.detach_model(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id!r} not found")
    return agent


@router.post("/{agent_id}/chat")
async def chat(
    agent_id: str,
    message: str = Form(...),
    k: int = Form(5),
    similarity_threshold: float = Form(0.7),
    history: str = Form(default="[]"),
    extra_context: str | None = Form(default=None),
    files: list[UploadFile] = File(default=[]),
    service: AgentService = Depends(),
) -> AgentChatResponse:
    agent = _get_agent_or_404(agent_id, service)
    if agent.status.value == "disabled":
        raise HTTPException(status_code=403, detail=f"Agent {agent.name!r} is disabled")
    try:
        parsed_history: list[dict] | None = None
        if history and history.strip() not in ("[]", ""):
            try:
                parsed_history = json.loads(history)
            except json.JSONDecodeError:
                raise HTTPException(status_code=422, detail="'history' must be a valid JSON array")

        chat_files = [
            (await f.read(), f.content_type or "", f.filename or "")
            for f in files
        ] if files else None

        return AgentChatService().chat(
            agent,
            message,
            k=k,
            similarity_threshold=similarity_threshold,
            files=chat_files,
            history=parsed_history,
            extra_context=extra_context,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
