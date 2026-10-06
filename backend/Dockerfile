FROM python:3.11-slim

<<<<<<< HEAD
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PORT=8000

WORKDIR /app

# Install system dependencies (for building packages, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
=======
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/backend

WORKDIR /backend

# Install system dependencies (build-essential, curl, libpq)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
<<<<<<< HEAD
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source code
=======
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
COPY . .

EXPOSE 8000

<<<<<<< HEAD
# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
=======
# Default command: run FastAPI backend with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
>>>>>>> 39ca26fcc1552ae7b4fa3efb7e2fc61729f97070
