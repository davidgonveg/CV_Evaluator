# Dockerfile para CV Evaluator
FROM python:3.11-slim

# Configurar directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (para aprovechar cache de Docker)
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Variables de entorno por defecto
ENV PYTHONPATH=/app
ENV OLLAMA_BASE_URL=http://host.docker.internal:11434
ENV LLM_PROVIDER=ollama
ENV LLM_MODEL=mistral:7b-instruct-q4_K_M

# Puerto de Streamlit
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Comando por defecto: ejecutar Streamlit
CMD ["streamlit", "run", "src/ui/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
