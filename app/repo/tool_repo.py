import json
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from app.models.tool.tool import CustomTool

_DEFAULT_TOOLS_PATH = "./data/tools.json"


def _tools_file() -> Path:
    return Path(_DEFAULT_TOOLS_PATH)


def _read_all() -> dict:
    path = _tools_file()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception as e:
        logger.error(f"Failed to read tools file: {e}")
        return {}


def _write_all(data: dict) -> None:
    path = _tools_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


class CustomToolRepo:

    def create(self, tool: CustomTool) -> CustomTool:
        data = _read_all()
        data[tool.tool_id] = tool.model_dump(mode="json")
        _write_all(data)
        return tool

    def get(self, tool_id: str) -> CustomTool | None:
        data = _read_all()
        entry = data.get(tool_id)
        if entry is None:
            return None
        return CustomTool(**entry)

    def get_all(self) -> list[CustomTool]:
        data = _read_all()
        return [CustomTool(**v) for v in data.values()]

    def update(self, tool: CustomTool) -> CustomTool:
        data = _read_all()
        if tool.tool_id not in data:
            logger.warning(f"update called for unknown tool_id {tool.tool_id}")
            return tool
        tool.updated_at = datetime.now(timezone.utc).isoformat()
        data[tool.tool_id] = tool.model_dump(mode="json")
        _write_all(data)
        return tool

    def delete(self, tool_id: str) -> bool:
        data = _read_all()
        if tool_id not in data:
            return False
        del data[tool_id]
        _write_all(data)
        return True
