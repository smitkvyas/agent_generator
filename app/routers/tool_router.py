from fastapi import APIRouter, Depends, HTTPException

from app.models.tool.tool import CreateToolRequest, CustomTool, UpdateToolRequest
from app.services.tool_service import CustomToolService

router = APIRouter(prefix="/tools", tags=["tools"])


def _get_tool_or_404(tool_id: str, service: CustomToolService) -> CustomTool:
    tool = service.get(tool_id)
    if tool is None:
        raise HTTPException(status_code=404, detail=f"Tool {tool_id!r} not found")
    return tool


@router.post("", status_code=201)
def create_tool(request: CreateToolRequest, service: CustomToolService = Depends()) -> CustomTool:
    return service.create(request)


@router.get("")
def list_tools(service: CustomToolService = Depends()) -> list[CustomTool]:
    return service.get_all()


@router.get("/{tool_id}")
def get_tool(tool_id: str, service: CustomToolService = Depends()) -> CustomTool:
    return _get_tool_or_404(tool_id, service)


@router.patch("/{tool_id}")
def update_tool(tool_id: str, request: UpdateToolRequest, service: CustomToolService = Depends()) -> CustomTool:
    tool = service.update(tool_id, request)
    if tool is None:
        raise HTTPException(status_code=404, detail=f"Tool {tool_id!r} not found")
    return tool


@router.delete("/{tool_id}", status_code=204)
def delete_tool(tool_id: str, service: CustomToolService = Depends()) -> None:
    if not service.delete(tool_id):
        raise HTTPException(status_code=404, detail=f"Tool {tool_id!r} not found")
