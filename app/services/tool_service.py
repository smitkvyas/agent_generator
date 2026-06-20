import uuid
from datetime import datetime, timezone

from app.models.tool.tool import CreateToolRequest, CustomTool, UpdateToolRequest
from app.repo.tool_repo import CustomToolRepo


class CustomToolService:

    def __init__(self):
        self._repo = CustomToolRepo()

    def create(self, request: CreateToolRequest) -> CustomTool:
        now = datetime.now(timezone.utc).isoformat()
        tool = CustomTool(
            tool_id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            endpoint_url=request.endpoint_url,
            http_method=request.http_method,
            headers=request.headers,
            created_at=now,
            updated_at=now,
        )
        return self._repo.create(tool)

    def get(self, tool_id: str) -> CustomTool | None:
        return self._repo.get(tool_id)

    def get_all(self) -> list[CustomTool]:
        return self._repo.get_all()

    def update(self, tool_id: str, request: UpdateToolRequest) -> CustomTool | None:
        tool = self._repo.get(tool_id)
        if tool is None:
            return None
        if request.name is not None:
            tool.name = request.name
        if request.description is not None:
            tool.description = request.description
        if request.endpoint_url is not None:
            tool.endpoint_url = request.endpoint_url
        if request.http_method is not None:
            tool.http_method = request.http_method
        if request.headers is not None:
            tool.headers = request.headers
        if request.parameters is not None:
            tool.parameters = request.parameters
        return self._repo.update(tool)

    def delete(self, tool_id: str) -> bool:
        return self._repo.delete(tool_id)
