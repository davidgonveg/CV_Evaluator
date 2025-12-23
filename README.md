# CV Evaluator - Sistema de Evaluacion de Candidatos con IA

Sistema basado en LLM para evaluar candidatos automaticamente analizando su CV contra los requisitos de una oferta de trabajo.

## Caracteristicas

- **Fase 1**: Analisis automatico de CV vs requisitos de oferta
- **Fase 2**: Entrevista interactiva para requisitos no encontrados
- **Arquitectura modular**: Facil intercambio de proveedores LLM (Ollama, OpenAI, Anthropic)
- **Interfaz web**: UI con Streamlit
- **Docker ready**: Despliegue sencillo con docker-compose

## Requisitos Previos

### 1. Instalar Ollama

Ollama permite ejecutar modelos LLM localmente sin coste.

**Windows (WSL):**
```bash
# En tu terminal WSL (Ubuntu)
curl -fsSL https://ollama.com/install.sh | sh
```

**Linux:**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Mac:**
```bash
brew install ollama
```

### 2. Descargar el modelo

```bash
# Iniciar Ollama (en una terminal separada)
ollama serve

# En otra terminal, descargar el modelo (7GB aprox)
ollama pull mistral:7b-instruct-q4_K_M
```

> **Nota**: El modelo `mistral:7b-instruct-q4_K_M` es una version cuantizada que funciona bien con 16GB de RAM en CPU. La primera ejecucion sera mas lenta mientras carga el modelo.

### 3. Python 3.10+

Asegurate de tener Python 3.10 o superior instalado.

## Instalacion

### Opcion A: Ejecucion local (recomendado para desarrollo)

```bash
# Crear entorno virtual
python -m venv venv 
# Dependiendo del python instalado, puede ser
# python3 -m venv venv  

# Activar entorno virtual
# En Linux/WSL/Mac:
source venv/bin/activate
# En Windows:
.\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Copiar configuracion
cp .env.example .env
```

### Opcion B: Docker (recomendado para produccion)

```bash
# Asegurate de que Ollama esta corriendo en el host
ollama serve

# Construir y ejecutar
docker-compose up --build
```

## Uso

### Interfaz Web (Streamlit)

```bash
# Asegurate de que Ollama esta corriendo
ollama serve  # En otra terminal

# Ejecutar la aplicacion
# Con entorno virtual activado:
PYTHONPATH=. streamlit run src/ui/streamlit_app.py

# O con Docker:
docker-compose up
```

Abre http://localhost:8501 en tu navegador.

### Terminal (CLI)

```bash
PYTHONPATH=. python -m src.main
```

## Como funciona

### Fase 1: Analisis del CV

1. El sistema parsea la oferta de trabajo y extrae los requisitos
2. Clasifica cada requisito como obligatorio u opcional
3. Analiza el CV y determina que requisitos cumple
4. Calcula la puntuacion: `(requisitos cumplidos / total) * 100`
5. Si falta un requisito obligatorio, el candidato es descartado (score = 0)

### Fase 2: Entrevista

1. Si el candidato no esta descartado y hay requisitos no encontrados
2. El sistema genera preguntas para cada requisito faltante
3. El candidato responde a cada pregunta
4. El sistema evalua las respuestas
5. Se recalcula la puntuacion final

## Estructura del Proyecto

```
cv_evaluator/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuracion
│   ├── main.py                # CLI
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py         # Modelos Pydantic
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── templates.py       # Prompts del sistema
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_service.py     # Abstraccion LLM
│   │   ├── cv_analyzer.py     # Fase 1
│   │   └── interviewer.py     # Fase 2
│   └── ui/
│       ├── __init__.py
│       └── streamlit_app.py   # Interfaz web
├── data/
│   ├── sample_cv.txt          # CV de ejemplo
│   └── sample_offer.txt       # Oferta de ejemplo
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Configuracion

Variables de entorno (`.env`):

| Variable | Descripcion | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | Proveedor LLM | `ollama` |
| `LLM_MODEL` | Modelo a usar | `mistral:7b-instruct-q4_K_M` |
| `LLM_TEMPERATURE` | Temperatura (0-2) | `0.1` |
| `OLLAMA_BASE_URL` | URL de Ollama | `http://localhost:11434` |

## Cambiar de Proveedor LLM

El sistema usa LangChain para abstraer el proveedor LLM. Para cambiar:

### Usar OpenAI (requiere API key de pago)

```bash
# .env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...

# Instalar dependencia
pip install langchain-openai
```

### Usar Anthropic (requiere API key de pago)

```bash
# .env
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-haiku-20240307
ANTHROPIC_API_KEY=sk-ant-...

# Instalar dependencia
pip install langchain-anthropic
```

## Solucion de Problemas

### Error de conexion con Ollama

```bash
# Verificar que Ollama esta corriendo
curl http://localhost:11434/api/tags

# Si no responde, iniciar Ollama
ollama serve
```

### Modelo no encontrado

```bash
# Descargar el modelo
ollama pull mistral:7b-instruct-q4_K_M

# Verificar modelos disponibles
ollama list
```

### Rendimiento lento

- La primera ejecucion carga el modelo en memoria (puede tardar 1-2 min)
- Las siguientes ejecuciones son mas rapidas
- Si es muy lento, prueba un modelo mas pequeño:
  ```bash
  ollama pull phi3:mini
  # Cambiar LLM_MODEL=phi3:mini en .env
  ```

## Modelos Recomendados para CPU

| Modelo | RAM minima | Calidad | Velocidad |
|--------|------------|---------|-----------|
| `phi3:mini` | 4GB | Buena | Rapida |
| `mistral:7b-instruct-q4_K_M` | 8GB | Muy buena | Media |
| `llama3.2:latest` | 8GB | Excelente | Media |
| `mixtral:8x7b-instruct-v0.1-q4_K_M` | 32GB | Excelente | Lenta |

## Licencia

Proyecto de prueba tecnica.
