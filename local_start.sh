docker stop rag-agents || true
docker rm rag-agents || true
docker rmi rag_agent_generator-rag-agents:latest || true
docker compose -f docker-compose-local.yml up -d
docker logs --tail 100 -f rag-agents