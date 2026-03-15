FROM python:3.11-slim

WORKDIR /app

# Install MCP server
COPY mcp-server/pyproject.toml mcp-server/pyproject.toml
COPY mcp-server/src/ mcp-server/src/

# Copy synthetic patient data for FHIR tools
COPY data/synthea/ data/synthea/

# Tell FHIR client where to find synthea data (pip install puts code in site-packages)
ENV HP_SYNTHEA_DATA_DIR=/app/data/synthea

RUN pip install --no-cache-dir ./mcp-server

EXPOSE 8000

CMD ["python", "-m", "healthpulse_mcp.server"]
