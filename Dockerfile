FROM python:3.11-slim

WORKDIR /app

# Install MCP server
COPY mcp-server/pyproject.toml mcp-server/pyproject.toml
COPY mcp-server/src/ mcp-server/src/

RUN pip install --no-cache-dir ./mcp-server

EXPOSE 8000

CMD ["python", "-m", "healthpulse_mcp.server"]
