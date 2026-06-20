import uuid
from datetime import datetime, timezone

from app.models.agent.agent import Agent, AgentStatus, CreateAgentRequest, UpdateAgentRequest
from app.repo.agent_repo import AgentRepo


class AgentService:

    def __init__(self):
        self._repo = AgentRepo()

    def create(self, request: CreateAgentRequest) -> Agent:
        now = datetime.now(timezone.utc).isoformat()
        agent = Agent(
            agent_id=str(uuid.uuid4()),
            name=request.name,
            system_prompt=request.system_prompt,
            status=AgentStatus.DISABLED,
            media_ids=request.media_ids,
            llm_provider=request.llm_provider,
            created_at=now,
            updated_at=now,
        )
        return self._repo.create(agent)

    def get(self, agent_id: str) -> Agent | None:
        return self._repo.get(agent_id)

    def get_all(self) -> list[Agent]:
        return self._repo.get_all()

    def update(self, agent_id: str, request: UpdateAgentRequest) -> Agent | None:
        agent = self._repo.get(agent_id)
        if agent is None:
            return None
        if request.name is not None:
            agent.name = request.name
        if request.system_prompt is not None:
            agent.system_prompt = request.system_prompt
        if request.llm_provider is not None:
            agent.llm_provider = request.llm_provider
        return self._repo.update(agent)

    def delete(self, agent_id: str) -> bool:
        return self._repo.delete(agent_id)

    def enable(self, agent_id: str) -> Agent | None:
        return self._repo.set_status(agent_id, AgentStatus.ENABLED)

    def disable(self, agent_id: str) -> Agent | None:
        return self._repo.set_status(agent_id, AgentStatus.DISABLED)

    def attach_media(self, agent_id: str, media_id: str) -> Agent | None:
        return self._repo.attach_media(agent_id, media_id)

    def detach_media(self, agent_id: str, media_id: str) -> Agent | None:
        return self._repo.detach_media(agent_id, media_id)

    def attach_tool(self, agent_id: str, tool_id: str) -> Agent | None:
        return self._repo.attach_tool(agent_id, tool_id)

    def detach_tool(self, agent_id: str, tool_id: str) -> Agent | None:
        return self._repo.detach_tool(agent_id, tool_id)

    def attach_model(self, agent_id: str, model_id: str, backup_model_id: str | None = None) -> Agent | None:
        return self._repo.attach_model(agent_id, model_id, backup_model_id=backup_model_id)

    def detach_model(self, agent_id: str) -> Agent | None:
        return self._repo.detach_model(agent_id)
