import json
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

from app.models.pipeline.pipeline import Pipeline

_DEFAULT_PIPELINES_PATH = "./data/pipelines.json"


def _file() -> Path:
    return Path(_DEFAULT_PIPELINES_PATH)


def _read_all() -> dict:
    path = _file()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception as e:
        logger.error(f"Failed to read pipelines file: {e}")
        return {}


def _write_all(data: dict) -> None:
    path = _file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


class PipelineRepo:

    def create(self, pipeline: Pipeline) -> Pipeline:
        data = _read_all()
        data[pipeline.pipeline_id] = pipeline.model_dump(mode="json")
        _write_all(data)
        return pipeline

    def get(self, pipeline_id: str) -> Pipeline | None:
        data = _read_all()
        entry = data.get(pipeline_id)
        if entry is None:
            return None
        return Pipeline(**entry)

    def get_all(self) -> list[Pipeline]:
        data = _read_all()
        return [Pipeline(**v) for v in data.values()]

    def update(self, pipeline: Pipeline) -> Pipeline:
        data = _read_all()
        if pipeline.pipeline_id not in data:
            logger.warning(f"update called for unknown pipeline_id {pipeline.pipeline_id}")
            return pipeline
        pipeline.updated_at = datetime.now(timezone.utc).isoformat()
        data[pipeline.pipeline_id] = pipeline.model_dump(mode="json")
        _write_all(data)
        return pipeline

    def delete(self, pipeline_id: str) -> bool:
        data = _read_all()
        if pipeline_id not in data:
            return False
        del data[pipeline_id]
        _write_all(data)
        return True

    def add_agent(self, pipeline_id: str, agent_id: str) -> Pipeline | None:
        data = _read_all()
        if pipeline_id not in data:
            return None
        if agent_id not in data[pipeline_id]["agent_ids"]:
            data[pipeline_id]["agent_ids"].append(agent_id)
            data[pipeline_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
            _write_all(data)
        return Pipeline(**data[pipeline_id])

    def remove_agent(self, pipeline_id: str, agent_id: str) -> Pipeline | None:
        data = _read_all()
        if pipeline_id not in data:
            return None
        data[pipeline_id]["agent_ids"] = [a for a in data[pipeline_id]["agent_ids"] if a != agent_id]
        if data[pipeline_id].get("entry_agent_id") == agent_id:
            data[pipeline_id]["entry_agent_id"] = None
        data[pipeline_id]["updated_at"] = datetime.now(timezone.utc).isoformat()
        _write_all(data)
        return Pipeline(**data[pipeline_id])
