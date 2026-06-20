from fastapi import APIRouter, Depends, HTTPException

from app.models.pipeline.pipeline import (
    CreatePipelineRequest,
    Pipeline,
    PipelineRunRequest,
    PipelineRunResponse,
    UpdatePipelineRequest,
)
from app.services.pipeline_run_service import PipelineRunService
from app.services.pipeline_service import PipelineService

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


def _get_pipeline_or_404(pipeline_id: str, service: PipelineService) -> Pipeline:
    pipeline = service.get(pipeline_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id!r} not found")
    return pipeline


@router.post("", status_code=201)
def create_pipeline(request: CreatePipelineRequest, service: PipelineService = Depends()) -> Pipeline:
    return service.create(request)


@router.get("")
def list_pipelines(service: PipelineService = Depends()) -> list[Pipeline]:
    return service.get_all()


@router.get("/{pipeline_id}")
def get_pipeline(pipeline_id: str, service: PipelineService = Depends()) -> Pipeline:
    return _get_pipeline_or_404(pipeline_id, service)


@router.patch("/{pipeline_id}")
def update_pipeline(pipeline_id: str, request: UpdatePipelineRequest, service: PipelineService = Depends()) -> Pipeline:
    pipeline = service.update(pipeline_id, request)
    if pipeline is None:
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id!r} not found")
    return pipeline


@router.delete("/{pipeline_id}", status_code=204)
def delete_pipeline(pipeline_id: str, service: PipelineService = Depends()) -> None:
    if not service.delete(pipeline_id):
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id!r} not found")


@router.post("/{pipeline_id}/agents/{agent_id}")
def add_agent(pipeline_id: str, agent_id: str, service: PipelineService = Depends()) -> Pipeline:
    pipeline = service.add_agent(pipeline_id, agent_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id!r} not found")
    return pipeline


@router.delete("/{pipeline_id}/agents/{agent_id}")
def remove_agent(pipeline_id: str, agent_id: str, service: PipelineService = Depends()) -> Pipeline:
    pipeline = service.remove_agent(pipeline_id, agent_id)
    if pipeline is None:
        raise HTTPException(status_code=404, detail=f"Pipeline {pipeline_id!r} not found")
    return pipeline


@router.post("/{pipeline_id}/run")
def run_pipeline(pipeline_id: str, request: PipelineRunRequest, service: PipelineService = Depends()) -> PipelineRunResponse:
    pipeline = _get_pipeline_or_404(pipeline_id, service)
    try:
        return PipelineRunService().run(pipeline, request.message, k=request.k, similarity_threshold=request.similarity_threshold)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
