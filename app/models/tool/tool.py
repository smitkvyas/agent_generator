from enum import Enum

from pydantic import BaseModel


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"


class ParamType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"


class ToolParameter(BaseModel):
    name: str
    type: ParamType = ParamType.STRING
    description: str
    required: bool = True


class CustomTool(BaseModel):
    tool_id: str
    name: str
    description: str
    endpoint_url: str
    http_method: HttpMethod = HttpMethod.POST
    headers: dict[str, str] = {}
    parameters: list[ToolParameter] = []
    created_at: str
    updated_at: str


class CreateToolRequest(BaseModel):
    name: str
    description: str
    endpoint_url: str
    http_method: HttpMethod = HttpMethod.POST
    headers: dict[str, str] = {}
    parameters: list[ToolParameter] = []


class UpdateToolRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    endpoint_url: str | None = None
    http_method: HttpMethod | None = None
    headers: dict[str, str] | None = None
    parameters: list[ToolParameter] | None = None
