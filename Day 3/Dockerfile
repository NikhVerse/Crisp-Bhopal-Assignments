FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the workspace root inside the container
WORKDIR /app

# Install system build dependencies (required for compiling ChromaDB/hnswlib if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements first to optimize build caching
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy all source files matching the local structure
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY .env ./

# Create data directories with appropriate permissions
RUN mkdir -p /app/backend/uploads /app/backend/vectorstore

# Set current directory to backend so that imports (app.*) resolve correctly
WORKDIR /app/backend

# Expose port
EXPOSE 8000

# Start FastAPI application using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
