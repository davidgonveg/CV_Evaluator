# CV Evaluator - Sistema de Evaluación de Candidatos con IA Gen

## Descripción del Proyecto

Este proyecto implementa un sistema inteligente basado en LLM (Large Language Models) diseñado para automatizar la evaluación de candidatos en procesos de selección.

### Objetivo
Diseñar un sistema capaz de:
1.  **Fase 1 (Análisis)**: Leer una oferta de trabajo y un CV, identificar requisitos cumplidos/no cumplidos y calcular una puntuación inicial.
2.  **Fase 2 (Entrevista)**: Entrevistar interactivamente al candidato sobre los requisitos no encontrados para completar la evaluación.

## Solución Implementada

El sistema ha sido desarrollado en **Python 3.11** utilizando **LangChain** para la orquestación de llamadas a LLMs. Es agnóstico al modelo, soportando Ollama (por defecto para ejecución local), OpenAI, Anthropic, etc.

### Flujo de Trabajo

1.  **Análisis de Oferta**: El sistema extrae requisitos individuales de la oferta, distinguiendo entre *obligatorios* (mandatory) y *opcionales* (optional). Descompone requisitos complejos (ej: "Python y Docker" -> 2 requisitos).
2.  **Evaluación de CV**:
    *   Compara cada requisito contra el texto del CV.
    *   **Matching**: El requisito se cumple claramente (soporte para typos y sinónimos).
    *   **Unmatching**: El candidato indica explícitamente que NO tiene la habilidad. **Descarta al candidato** si el requisito es obligatorio.
    *   **Not Found**: El requisito no se menciona o es ambiguo. **No descarta** (se preguntará en la entrevista).
3.  **Cálculo de Score Inicial**: Porcentaje de requisitos cumplidos sobre el total.
4.  **Entrevista Dinámica**:
    *   Un agente de IA genera preguntas específicas para cada requisito "Not Found".
    *   Evalúa las respuestas del candidato en tiempo real.
    *   Actualiza el estado de los requisitos (de "Not Found" a "Matching" o "Unmatching").
5.  **Score Final**: Recálculo de la puntuación con la nueva información.

### Puntos Fuertes Técnicos
*   **Prompt Engineering Avanzado**: Se han implementado técnicas de "Chain of Thought" implícito en los prompts para manejar casos complejos:
    *   **Tolerancia a Typos**: Reconoce "Kubernets" como "Kubernetes".
    *   **Inferencia de Contexto**: Deduce habilidades implícitas (ej: "Native Speaker" -> Inglés Alto).
    *   **Detección de Negativas**: Identifica explícitamente "React: Nulo" como un descarte, no como "no encontrado".
    *   **Desambiguación de Roles**: Distingue entre gestionar un equipo (PM) y tener la habilidad técnica.
*   **Arquitectura Modular**: Separación clara entre lógica de negocio (`services`), modelos de datos (`models`) e interfaz (`ui`).
*   **Testing Robusto**: Incluye una suite de tests complejos (`tests/run_complex_tests.py`) que valida la resiliencia del sistema ante casos borde.

---

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

> **Nota**: El modelo `mistral:7b-instruct-q4_K_M` es una versión cuantizada que funciona bien con 16GB de RAM en CPU. La primera ejecución será más lenta mientras carga el modelo.

### 3. Python 3.10+

Asegúrate de tener Python 3.10 o superior instalado.

## Instalación

### Opción A: Ejecución local (recomendado para desarrollo)

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

# Copiar configuración
cp .env.example .env
```

### Opción B: Docker (recomendado para producción)

```bash
# Asegúrate de que Ollama está corriendo en el host
ollama serve

# Construir y ejecutar
docker-compose up --build
```

## Uso

### Interfaz Web (Streamlit)

```bash
# Asegúrate de que Ollama está corriendo
ollama serve  # En otra terminal

# Ejecutar la aplicación
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

### Ejecutar Tests

Para validar la robustez del sistema:

```bash
PYTHONPATH=. python tests/run_complex_tests.py
```

## Estructura del Proyecto

```
cv_evaluator/
├── src/
│   ├── models/        # Esquemas Pydantic (JobOffer, CVResult...)
│   ├── prompts/       # Templates de Prompts optimizados
│   ├── services/      # Lógica Core
│   │   ├── cv_analyzer.py     # Lógica de Fase 1
│   │   ├── interviewer.py     # Lógica de Fase 2 (Agente)
│   │   └── llm_service.py     # Abstracción de LangChain
│   └── ui/            # Interfaz Streamlit
├── tests/             # Suite de pruebas complejas
├── data/              # Datos de ejemplo
├── Dockerfile         # Configuración Docker
└── requirements.txt   # Dependencias
```

## Configuración

Variables de entorno (`.env`):

| Variable | Descripción | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | Proveedor LLM | `ollama` |
| `LLM_MODEL` | Modelo a usar | `mistral:7b-instruct-q4_K_M` |
| `OLLAMA_BASE_URL` | URL de Ollama | `http://localhost:11434` |
