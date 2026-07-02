FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    SOARINGSPOT_MCP_TRANSPORT=http \
    SOARINGSPOT_MCP_HOST=0.0.0.0 \
    SOARINGSPOT_MCP_PORT=9009 \
    SOARINGSPOT_MCP_PATH=/soaringspot\
    SOARINGSPOT_API_URL=http://localhost:8000 \
    SOARINGSPOT_HTTP_TIMEOUT_SEC=60 \
    SOARINGSPOT_TOKEN_MIN_VALIDITY_SEC=30 \
    SOARINGSPOT_VERIFY_TLS=true

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ss_server.py ./
COPY .env        ./

EXPOSE 9009

CMD ["python", "ss_server.py", "--host", "0.0.0.0", "--port", "9009", "--path","/soaringspot"]

