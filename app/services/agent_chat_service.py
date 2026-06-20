import os
import tempfile

from loguru import logger

from app.models.agent.agent import Agent, AgentChatResponse
from app.repo.model_config_repo import ModelConfigRepo
from app.repo.tool_repo import CustomToolRepo
from app.services.rag_search_service import RAGSearchService
from src.genai.llm_call import make_llm_call
from src.pdf_processing.pdf_processor import PDFProcessor
from src.tools.tool_builder import build_langchain_tool

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tiff"}
_PDF_EXTENSION = ".pdf"

# ChatFile: (raw_bytes, mime_type, filename)
ChatFile = tuple[bytes, str, str]


class AgentChatService:

    def chat(
        self,
        agent: Agent,
        message: str,
        k: int = 5,
        similarity_threshold: float = 0.7,
        files: list[ChatFile] | None = None,
        history: list[dict] | None = None,
        extra_context: str | None = None,
    ) -> AgentChatResponse:
        system_prompt, rag_chunks_used = self._build_system_prompt(agent, message, k, similarity_threshold)

        if extra_context and extra_context.strip():
            system_prompt += f"\n\nAdditional context:\n\n{extra_context.strip()}"

        images: list[tuple[bytes, str]] = []
        if files:
            pdf_texts, images = self._process_chat_files(files)
            if pdf_texts:
                doc_context = "\n\n---\n\n".join(pdf_texts)
                system_prompt += f"\n\nContent from uploaded documents:\n\n{doc_context}"

        logger.info(
            f"Agent {agent.name!r} chat | media_ids={agent.media_ids} "
            f"rag_chunks={rag_chunks_used} images={len(images)} "
            f"history_turns={len(history) if history else 0}"
        )

        lc_tools = self._resolve_tools(agent.tool_ids)
        primary_model = self._resolve_model_name(agent.model_id)

        try:
            llm_response = make_llm_call(
                agent.llm_provider,
                message,
                system_prompt=system_prompt,
                images=images or None,
                history=history or None,
                tools=lc_tools or None,
                model_name=primary_model,
            )
        except Exception as e:
            backup_model = self._resolve_model_name(agent.backup_model_id)
            if backup_model is None:
                raise RuntimeError(f"LLM call failed: {e}") from e
            logger.warning(f"Primary model failed ({e!r}), retrying with backup {backup_model!r}")
            llm_response = make_llm_call(
                agent.llm_provider,
                message,
                system_prompt=system_prompt,
                images=images or None,
                history=history or None,
                tools=lc_tools or None,
                model_name=backup_model,
            )

        return AgentChatResponse(
            agent_id=agent.agent_id,
            agent_name=agent.name,
            message=message,
            response=llm_response.content,
            model=llm_response.model,
            provider=llm_response.provider,
            input_tokens=llm_response.input_tokens,
            output_tokens=llm_response.output_tokens,
            total_tokens=llm_response.total_tokens,
            rag_chunks_used=rag_chunks_used,
        )

    def _process_chat_files(
        self, files: list[ChatFile]
    ) -> tuple[list[str], list[tuple[bytes, str]]]:
        """Extract text from PDFs and collect raw bytes from images."""
        pdf_texts: list[str] = []
        images: list[tuple[bytes, str]] = []

        for raw, mime_type, filename in files:
            ext = os.path.splitext(filename.lower())[1]

            if ext == _PDF_EXTENSION or mime_type == "application/pdf":
                text = self._extract_pdf_text(raw, filename)
                if text.strip():
                    pdf_texts.append(f"[{filename}]\n{text}")
            elif ext in _IMAGE_EXTENSIONS or mime_type.startswith("image/"):
                resolved_mime = mime_type if mime_type.startswith("image/") else "image/jpeg"
                images.append((raw, resolved_mime))
            else:
                logger.warning(f"Unsupported file type in chat: {filename!r}, skipping")

        return pdf_texts, images

    def _extract_pdf_text(self, raw: bytes, filename: str) -> str:
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(raw)
                tmp_path = tmp.name
            with PDFProcessor(tmp_path) as processor:
                return processor.extract_text()
        except Exception as e:
            logger.warning(f"Failed to extract text from PDF {filename!r}: {e}")
            return ""
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _resolve_model_name(self, model_id: str | None) -> str | None:
        if model_id is None:
            return None
        config = ModelConfigRepo().get(model_id)
        if config is None:
            logger.warning(f"Model config {model_id!r} not found, falling back to default")
            return None
        return config.model_name

    def _resolve_tools(self, tool_ids: list[str]) -> list:
        if not tool_ids:
            return []
        repo = CustomToolRepo()
        tools = []
        for tool_id in tool_ids:
            tool_config = repo.get(tool_id)
            if tool_config is not None:
                tools.append(build_langchain_tool(tool_config))
            else:
                logger.warning(f"Tool {tool_id!r} not found, skipping")
        return tools

    def _build_system_prompt(
        self, agent: Agent, message: str, k: int, similarity_threshold: float
    ) -> tuple[str, int]:
        system = agent.system_prompt
        rag_chunks_used = 0

        if not agent.media_ids:
            return system, rag_chunks_used

        rag_service = RAGSearchService()
        chunks: list[str] = []

        for media_id in agent.media_ids:
            try:
                result = rag_service.search(
                    message,
                    k=k,
                    similarity_threshold=similarity_threshold,
                    media_id=media_id,
                )
                for r in result.results:
                    source = r.metadata.get("source", "")
                    chunks.append(f"[{source}]\n{r.content}" if source else r.content)
            except RuntimeError as e:
                logger.warning(f"RAG search skipped for media_id={media_id}: {e}")

        for chunk in chunks:
            logger.debug(f"RAG chunk : {chunk}...")

        if chunks:
            context = "\n\n---\n\n".join(chunks)
            system = f"{system}\n\nRelevant context from attached documents:\n\n{context}"
            rag_chunks_used = len(chunks)

        return system, rag_chunks_used
