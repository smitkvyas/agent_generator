import base64
from dataclasses import dataclass
from datetime import datetime

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from loguru import logger

from app.utils.env_utils import Env
from src.genai.GENAI_CONFIG import GROQ_DEFAULT_MODEL, GROQ_VISION_MODEL
from src.genai.llm import load_llm_groq


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str
    finish_reason: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    completion_time_s: float
    total_time_s: float


def get_model(provider_name: str):
    if provider_name == "groq":
        return GROQ_DEFAULT_MODEL
    else:
        return load_llm_groq()


def _extract_response_metadata(ai_msg: AIMessage, llm_provider_name: str) -> LLMResponse:
    rm = ai_msg.response_metadata
    token_usage = rm.get("token_usage", {})
    return LLMResponse(
        content=ai_msg.content,
        model=rm.get("model_name", ""),
        provider=rm.get("model_provider", llm_provider_name),
        finish_reason=rm.get("finish_reason", ""),
        input_tokens=token_usage.get("prompt_tokens", ai_msg.usage_metadata.get("input_tokens", 0)),
        output_tokens=token_usage.get("completion_tokens", ai_msg.usage_metadata.get("output_tokens", 0)),
        total_tokens=token_usage.get("total_tokens", ai_msg.usage_metadata.get("total_tokens", 0)),
        completion_time_s=token_usage.get("completion_time", 0.0),
        total_time_s=token_usage.get("total_time", 0.0),
    )


def _history_to_lc_messages(history: list[dict]) -> list:
    """Convert [{"role": "user"|"assistant", "content": "..."}] to LangChain messages."""
    lc = []
    for msg in history:
        role, content = msg.get("role", ""), msg.get("content", "")
        if role == "user":
            lc.append(HumanMessage(content=content))
        elif role == "assistant":
            lc.append(AIMessage(content=content))
    return lc


def make_llm_call(
    llm_provider_name: str,
    prompt: str,
    system_prompt: str | None = None,
    images: list[tuple[bytes, str]] | None = None,
    history: list[dict] | None = None,
    tools: list | None = None,
    model_name: str | None = None,
) -> LLMResponse:
    """
    Args:
        llm_provider_name: LLM provider (e.g. "groq")
        prompt: Current user message
        system_prompt: Optional system instructions (with RAG context pre-injected)
        images: Optional list of (raw_bytes, mime_type) for vision input
        history: Optional prior turns as [{"role": "user"|"assistant", "content": "..."}]
    """
    api_key = Env.get("GROQ_API_KEY", required=True)
    if not api_key or not api_key.strip():
        raise RuntimeError("GROQ_API_KEY is set but empty — add your key to .env")

    logger.info(
        f"Executing LLM call | images={len(images) if images else 0} "
        f"history_turns={len(history) if history else 0} | query={prompt[:80]!r}"
    )
    start = datetime.now()

    if system_prompt:
        logger.debug(f"[SYSTEM PROMPT]\n{system_prompt}")
    if history:
        for i, msg in enumerate(history):
            logger.debug(f"[HISTORY {i+1}/{len(history)} | {msg.get('role', '?')}]\n{msg.get('content', '')}")
    logger.debug(f"[USER MESSAGE]\n{prompt}")

    if images:
        lc_messages = []
        if system_prompt:
            lc_messages.append(SystemMessage(content=system_prompt))
        if history:
            lc_messages.extend(_history_to_lc_messages(history))

        content: list = [{"type": "text", "text": prompt}]
        for img_bytes, mime_type in images:
            b64 = base64.b64encode(img_bytes).decode()
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{b64}"},
            })
        lc_messages.append(HumanMessage(content=content))

        llm = load_llm_groq(model=GROQ_VISION_MODEL)
        ai_msg: AIMessage = llm.invoke(lc_messages)
    else:
        dict_messages: list[dict] = []
        if system_prompt:
            dict_messages.append({"role": "system", "content": system_prompt})
        if history:
            dict_messages.extend(history)
        dict_messages.append({"role": "user", "content": prompt})

        resolved_model = f"groq:{model_name}" if model_name else get_model(llm_provider_name)
        agent = create_agent(model=resolved_model, tools=tools or [])
        raw = agent.invoke({"messages": dict_messages})
        ai_msg = raw["messages"][-1]

    response = _extract_response_metadata(ai_msg, llm_provider_name)
    logger.debug(f"[RESPONSE]\n{response.content}")
    logger.info(
        f"LLM call completed in {datetime.now() - start} | "
        f"input_tokens={response.input_tokens} output_tokens={response.output_tokens} total_tokens={response.total_tokens} | "
        f"context: system_prompt={len(system_prompt) if system_prompt else 0} chars "
        f"history_turns={len(history) if history else 0} "
        f"message={len(prompt)} chars"
    )
    return response
