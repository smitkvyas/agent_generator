import uuid
from datetime import datetime, timezone

from app.models.pipeline.pipeline import CreatePipelineRequest, Pipeline, UpdatePipelineRequest
from app.repo.pipeline_repo import PipelineRepo


class PipelineService:

    def __init__(self):
        self._repo = PipelineRepo()

    def create(self, request: CreatePipelineRequest) -> Pipeline:
        now = datetime.now(timezone.utc).isoformat()
        pipeline = Pipeline(
            pipeline_id=str(uuid.uuid4()),
            name=request.name,
            mode=request.mode,
            agent_ids=request.agent_ids,
            entry_agent_id=request.entry_agent_id,
            created_at=now,
            updated_at=now,
        )
        return self._repo.create(pipeline)

    def get(self, pipeline_id: str) -> Pipeline | None:
        return self._repo.get(pipeline_id)

    def get_all(self) -> list[Pipeline]:
        return self._repo.get_all()

    def update(self, pipeline_id: str, request: UpdatePipelineRequest) -> Pipeline | None:
        pipeline = self._repo.get(pipeline_id)
        if pipeline is None:
            return None
        if request.name is not None:
            pipeline.name = request.name
        if request.mode is not None:
            pipeline.mode = request.mode
        if request.entry_agent_id is not None:
            pipeline.entry_agent_id = request.entry_agent_id
        return self._repo.update(pipeline)

    def delete(self, pipeline_id: str) -> bool:
        return self._repo.delete(pipeline_id)

    def add_agent(self, pipeline_id: str, agent_id: str) -> Pipeline | None:
        return self._repo.add_agent(pipeline_id, agent_id)

    def remove_agent(self, pipeline_id: str, agent_id: str) -> Pipeline | None:
        return self._repo.remove_agent(pipeline_id, agent_id)
