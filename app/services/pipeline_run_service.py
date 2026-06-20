from loguru import logger

from app.models.pipeline.pipeline import (
    Pipeline,
    PipelineMode,
    PipelineRunResponse,
    PipelineStepResult,
)
from app.repo.agent_repo import AgentRepo
from app.services.agent_chat_service import AgentChatService

_MAX_ROUTER_HOPS = 10

_ROUTER_INJECTION = (
    "ROUTING INSTRUCTIONS: After your response, if you want to hand off to another agent, "
    "add 'ROUTE_TO: <agent_name>' on a new line at the very end. "
    "Available agents: {agents}. If no routing is needed, omit ROUTE_TO entirely."
)


class PipelineRunService:

    def run(self, pipeline: Pipeline, message: str, k: int = 5, similarity_threshold: float = 0.7) -> PipelineRunResponse:
        if pipeline.mode == PipelineMode.SEQUENTIAL:
            steps = self._run_sequential(pipeline, message, k, similarity_threshold)
        else:
            steps = self._run_router(pipeline, message, k, similarity_threshold)

        final_response = steps[-1].output if steps else ""
        return PipelineRunResponse(
            pipeline_id=pipeline.pipeline_id,
            pipeline_name=pipeline.name,
            mode=pipeline.mode,
            steps=steps,
            final_response=final_response,
            total_input_tokens=sum(s.input_tokens for s in steps),
            total_output_tokens=sum(s.output_tokens for s in steps),
            total_tokens=sum(s.total_tokens for s in steps),
        )

    def _run_sequential(self, pipeline: Pipeline, message: str, k: int, similarity_threshold: float) -> list[PipelineStepResult]:
        repo = AgentRepo()
        steps = []
        current_input = message

        for agent_id in pipeline.agent_ids:
            agent = repo.get(agent_id)
            if agent is None:
                logger.warning(f"Agent {agent_id!r} not found, skipping")
                continue
            if agent.status.value == "disabled":
                logger.warning(f"Agent {agent.name!r} is disabled, skipping")
                continue

            response = AgentChatService().chat(agent, current_input, k=k, similarity_threshold=similarity_threshold)
            steps.append(PipelineStepResult(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                input=current_input,
                output=response.response,
                model=response.model,
                provider=response.provider,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                total_tokens=response.total_tokens,
                rag_chunks_used=response.rag_chunks_used,
            ))
            current_input = response.response

        return steps

    def _run_router(self, pipeline: Pipeline, message: str, k: int, similarity_threshold: float) -> list[PipelineStepResult]:
        repo = AgentRepo()

        name_to_id: dict[str, str] = {}
        for aid in pipeline.agent_ids:
            agent = repo.get(aid)
            if agent:
                name_to_id[agent.name] = agent.agent_id

        steps = []
        current_input = message
        current_agent_id = pipeline.entry_agent_id
        visited: set[str] = set()

        while current_agent_id and len(steps) < _MAX_ROUTER_HOPS:
            if current_agent_id in visited:
                logger.warning(f"Loop detected at agent {current_agent_id!r}, stopping")
                break
            visited.add(current_agent_id)

            agent = repo.get(current_agent_id)
            if agent is None or agent.status.value == "disabled":
                logger.warning(f"Agent {current_agent_id!r} unavailable, stopping")
                break

            routing_hint = _ROUTER_INJECTION.format(agents=", ".join(name_to_id.keys()))
            response = AgentChatService().chat(
                agent, current_input,
                k=k, similarity_threshold=similarity_threshold,
                extra_context=routing_hint,
            )

            raw_output = response.response
            next_agent_id = None

            if "ROUTE_TO:" in raw_output:
                clean_lines = []
                for line in raw_output.split("\n"):
                    if line.strip().startswith("ROUTE_TO:"):
                        agent_name = line.split("ROUTE_TO:", 1)[1].strip()
                        next_agent_id = name_to_id.get(agent_name)
                        if not next_agent_id:
                            logger.warning(f"ROUTE_TO agent {agent_name!r} not found in pipeline")
                    else:
                        clean_lines.append(line)
                raw_output = "\n".join(clean_lines).strip()

            steps.append(PipelineStepResult(
                agent_id=agent.agent_id,
                agent_name=agent.name,
                input=current_input,
                output=raw_output,
                model=response.model,
                provider=response.provider,
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                total_tokens=response.total_tokens,
                rag_chunks_used=response.rag_chunks_used,
            ))
            current_input = raw_output if raw_output else current_input
            current_agent_id = next_agent_id

        return steps
