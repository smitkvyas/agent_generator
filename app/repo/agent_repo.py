import json
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from app.models.agent.agent import Agent, AgentStatus
from app.utils.env_utils import Env

_DEFAULT_AGENTS_PATH = "./data/agents.json"


def _agents_file() -> Path:
    return Path(Env.get("AGENTS_PATH", _DEFAULT_AGENTS_PATH))


def _read_all() -> dict:
    path = _agents_file()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception as e:
        logger.error(f"Failed to read agents file: {e}")
        return {}


def _write_all(data: dict) -> None:
    path = _agents_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


class AgentRepo:

    def create(self, agent: Agent) -> Agent:
        data = _read_all()
        data[agent.agent_id] = agent.model_dump(mode="json")
        _write_all(data)
        return agent

    def get(self, agent_id: str) -> Agent | None:
        data = _read_all()
        entry = data.get(agent_id)
        if entry is None:
            return None
        return Agent(**entry)

    def get_all(self) -> list[Agent]:
        data = _read_all()
        return [Agent(**v) for v in data.values()]

    def update(self, agent: Agent) -> Agent:
        data = _read_all()
        if agent.agent_id not in data:
            logger.warning(f"update called for unknown agent_id {agent.agent_id}")
            return agent
        agent.updated_at = datetime.now(timezone.utc).isoformat()
        data[agent.agent_id] = agent.model_dump(mode="json")
        _write_all(data)
        return agent

    def delete(self, agent_id: str) -> bool:
        data = _read_all()
        if agent_id not in data:
            return False
        del data[agent_id]
        _write_all(data)
        return True

    def set_status(self, agent_id: str, status: AgentStatus) -> Agent | None:
        data = _read_all()
        if agent_id not in data:
            return None
        data[agent_id]["status"] = status.value
        data[agent_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        _write_all(data)
        return Agent(**data[agent_id])

    def attach_media(self, agent_id: str, media_id: str) -> Agent | None:
        data = _read_all()
        if agent_id not in data:
            return None
        if media_id not in data[agent_id]["media_ids"]:
            data[agent_id]["media_ids"].append(media_id)
            data[agent_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            _write_all(data)
        return Agent(**data[agent_id])

    def detach_media(self, agent_id: str, media_id: str) -> Agent | None:
        data = _read_all()
        if agent_id not in data:
            return None
        data[agent_id]["media_ids"] = [m for m in data[agent_id]["media_ids"] if m != media_id]
        data[agent_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        _write_all(data)
        return Agent(**data[agent_id])

    def attach_tool(self, agent_id: str, tool_id: str) -> Agent | None:
        data = _read_all()
        if agent_id not in data:
            return None
        if "tool_ids" not in data[agent_id]:
            data[agent_id]["tool_ids"] = []
        if tool_id not in data[agent_id]["tool_ids"]:
            data[agent_id]["tool_ids"].append(tool_id)
            data[agent_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            _write_all(data)
        return Agent(**data[agent_id])

    def detach_tool(self, agent_id: str, tool_id: str) -> Agent | None:
        data = _read_all()
        if agent_id not in data:
            return None
        data[agent_id]["tool_ids"] = [t for t in data[agent_id].get("tool_ids", []) if t != tool_id]
        data[agent_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        _write_all(data)
        return Agent(**data[agent_id])

    def attach_model(self, agent_id: str, model_id: str, backup_model_id: str | None = None) -> Agent | None:
        data = _read_all()
        if agent_id not in data:
            return None
        data[agent_id]["model_id"] = model_id
        data[agent_id]["backup_model_id"] = backup_model_id
        data[agent_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        _write_all(data)
        return Agent(**data[agent_id])

    def detach_model(self, agent_id: str) -> Agent | None:
        data = _read_all()
        if agent_id not in data:
            return None
        data[agent_id]["model_id"] = None
        data[agent_id]["backup_model_id"] = None
        data[agent_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        _write_all(data)
        return Agent(**data[agent_id])
