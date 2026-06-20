import re

import requests
from langchain_core.tools import StructuredTool
from loguru import logger
from pydantic import BaseModel, Field, create_model

from app.models.tool.tool import CustomTool, HttpMethod, ParamType, ToolParameter

_PARAM_TYPE_MAP = {
    ParamType.STRING: str,
    ParamType.INTEGER: int,
    ParamType.NUMBER: float,
    ParamType.BOOLEAN: bool,
}


class _DefaultInput(BaseModel):
    input: str = Field(description="Input to send to the tool endpoint")


def _build_args_schema(parameters: list[ToolParameter]) -> type[BaseModel]:
    if not parameters:
        return _DefaultInput

    fields = {}
    for param in parameters:
        py_type = _PARAM_TYPE_MAP.get(param.type, str)
        if param.required:
            fields[param.name] = (py_type, Field(description=param.description))
        else:
            fields[param.name] = (py_type | None, Field(default=None, description=param.description))

    return create_model("ToolInput", **fields)


def build_langchain_tool(tool: CustomTool) -> StructuredTool:
    """Wrap a CustomTool config into a LangChain StructuredTool that calls the endpoint at runtime."""

    tool_id = tool.tool_id
    endpoint_url = tool.endpoint_url
    http_method = tool.http_method
    headers = dict(tool.headers)
    args_schema = _build_args_schema(tool.parameters)

    path_params = set(re.findall(r"\{(\w+)\}", endpoint_url))

    def call_endpoint(**kwargs) -> str:
        try:
            url = endpoint_url.format(**{k: kwargs[k] for k in path_params if k in kwargs})
            payload = {k: v for k, v in kwargs.items() if k not in path_params}
            if http_method == HttpMethod.GET:
                resp = requests.get(url, params=payload, headers=headers, timeout=30)
            else:
                resp = requests.post(url, json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            logger.warning(f"Tool {tool_id!r} call failed: {e}")
            return f"Tool call failed: {e}"

    safe_name = tool.name.strip().replace(" ", "_")

    return StructuredTool.from_function(
        func=call_endpoint,
        name=safe_name,
        description=tool.description,
        args_schema=args_schema,
    )
