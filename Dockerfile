# ==============================================================================
# LifeBridge AI — Production Container Definition (Cloud Run Ready)
# Multi-stage / minimal footprint, non-root security, $PORT compliant
# ==============================================================================

FROM python:3.12-slim AS runtime

# Set security and performance environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    HOST=0.0.0.0

# Create dedicated non-root user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

WORKDIR /home/appuser/app

# Install dependencies first for maximum layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy only essential application and static assets
COPY app/ ./app/
COPY static/ ./static/

# Set strict ownership and permissions
RUN chown -R appuser:appgroup /home/appuser/app

# Switch to non-root execution
USER appuser:appgroup

# Informational port declaration
EXPOSE 8080

# Health check using Python urllib (no curl/wget dependency required)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:' + str('${PORT}') + '/health')" || exit 1

# Launch uvicorn dynamically bound to 0.0.0.0 and Cloud Run's injected $PORT
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
