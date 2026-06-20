# Agent Generator

A FastAPI-based service for building and running retrieval-augmented generation (RAG) agents backed by FAISS and Hugging Face embeddings.

## Overview

This repository provides a backend API for:
- ingesting media files (PDF, image formats) for RAG indexing
- performing semantic search over indexed content
- configuring and managing generative agents
- attaching tools, media, and model configs to agents
- building and running agent pipelines

The project uses FastAPI, LangChain, FAISS, and Hugging Face embeddings to power the search and agent workflows.

## Key Features

- `POST /media/process-for-rag` - upload documents and images for background RAG processing
- `GET /media/status` - retrieve processing status for uploaded media
- `GET /media/{media_id}/chunks` - inspect the indexed chunks for a media item
- `POST /rag/search` - run similarity search against the RAG vector store
- `POST /agents` - create a new agent configuration
- `POST /agents/{agent_id}/chat` - send a chat request to an agent with optional retrieval context
- `POST /pipelines/{pipeline_id}/run` - execute a configured agent pipeline
- CRUD routes for tools, models, pipelines, agents, and media associations

## Repo Structure

- `app/` - FastAPI application, routers, services, repositories, and models
- `src/` - RAG search and processing utilities, embedding and vector store helpers
- `data/` - sample JSON records and FAISS index storage
- `requirements.txt` - Python dependencies for local development

## Getting Started

### Prerequisites

- Python 3.11+ recommended
- `pip` package manager
- Optional: Docker and Docker Compose for containerized startup

### Install dependencies

```bash
python -m pip install -r requirements.txt
```

### Run locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Run with Docker Compose

```bash
docker compose up --build
```

or if using local compose:

```bash
./local_start.sh
```

## Environment

The app uses environment variables for configuration. Common variables:
- `FAISS_DIR_PATH` - path to local FAISS index directory

## API Documentation

FastAPI automatically exposes interactive docs at:
- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## Notes

- The service loads Hugging Face embeddings and a local FAISS database during startup.
- Media processing runs in the background after upload, then content becomes searchable via the vector store.
- The repository is designed for experimentation with RAG-enabled agents and pipelines.

## License

This project does not include a license file. Add one if you want to open-source it.
