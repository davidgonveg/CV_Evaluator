"""Templates de prompts para las diferentes fases del sistema."""

# =============================================================================
# FASE 0: PARSEO DE LA OFERTA
# =============================================================================

PARSE_OFFER_PROMPT = """Eres un experto en recursos humanos analizando ofertas de trabajo.

Tu tarea es analizar la siguiente oferta de trabajo y extraer TODOS los requisitos individuales.

REGLAS IMPORTANTES:
1. Si un requisito menciona varias tecnologías/conocimientos separados por "y" o comas, SEPÁRALOS en requisitos individuales.
   Ejemplo: "Conocimientos en FastAPI y LangChain" -> Dos requisitos separados
2. Identifica si cada requisito es OBLIGATORIO (mandatory) u OPCIONAL (optional):
   - OBLIGATORIO: Palabras como "mínimo", "requerido", "obligatorio", "imprescindible", "necesario"
   - OPCIONAL: Palabras como "valorable", "deseable", "plus", "opcional", "se valorará"
3. Extrae el requisito de forma clara y concisa.

OFERTA DE TRABAJO:
{offer_text}

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta (sin explicaciones adicionales):
{{
    "requirements": [
        {{
            "description": "Descripción clara del requisito",
            "requirement_type": "mandatory" o "optional"
        }}
    ]
}}
"""

# =============================================================================
# FASE 1: EVALUACIÓN DEL CV
# =============================================================================

EVALUATE_CV_PROMPT = """Eres un experto en recursos humanos evaluando candidatos.

Tu tarea es analizar si el CV del candidato cumple cada uno de los requisitos de la oferta.

REQUISITOS DE LA OFERTA:
{requirements_json}

CV DEL CANDIDATO:
{cv_text}

INSTRUCCIONES:
1. Para cada requisito, determina si el CV lo cumple, no lo cumple, o no hay información suficiente.
2. Sé riguroso pero justo en la evaluación.
3. IMPORTANTE para detectar conocimientos:
   - Si el CV dice "El candidato tiene conocimientos en X" -> el candidato CUMPLE cualquier requisito sobre X
   - Si una tecnología aparece mencionada en experiencia laboral o habilidades -> CUMPLE
   - El nombre exacto de la tecnología es suficiente (ej: "FastAPI" en CV cumple requisito de "FastAPI")
4. Criterios de evaluación (SIGUE ESTE ORDEN):
   
   PASO 1: Busca PALABRAS CLAVE NEGATIVAS (Prioridad Máxima).
   - Si dice "React: Nulo", "Java: No", "Sin experiencia en X", "Nunca he usado X".
   - ESTADO: "unmatching". (Aunque aparezca la palabra, si el contexto es negativo, es unmatching).

   PASO 2: Busca EVIDENCIA POSITIVA (Certificaciones y Habilidades).
   - CERTIFICACIONES: "AWS Solutions Architect" -> CUMPLE requisito "AWS".
   - HABILIDADES EXPLÍCITAS: "Experto en Python", "Uso diario de Docker".
   - ESTADO: "matching".
   - TOLERANCIA: "Pythen" vale por "Python". "Kubernets" vale por "Kubernetes".

   PASO 3: Evalúa ROLES AMBIGUOS.
   - Si el candidato fue "Project Manager", "Product Owner" o "Scrum Master" en un equipo de "Java":
   - ¿Menciona explícitamente en la descripción que ÉL programaba?
     * SÍ -> "matching".
     * NO -> "not_found" (Asume que gestionaba, no programaba).

   PASO 4: Inferencia.
   - "Native English speaker" -> CUMPLE "Inglés alto".
   
   Si no encaja en ninguno de los anteriores -> "not_found".

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
    "evaluations": [
        {{
            "requirement": "Descripción del requisito",
            "requirement_type": "mandatory" o "optional",
            "status": "matching" | "unmatching" | "not_found",
            "reasoning": "Breve explicación de por qué"
        }}
    ]
}}
"""

# =============================================================================
# FASE 2: ENTREVISTA
# =============================================================================

GENERATE_GREETING_PROMPT = """Eres un entrevistador amable y profesional de recursos humanos.

Genera un saludo breve y cordial para iniciar una entrevista con un candidato.
Menciona que vas a hacerle algunas preguntas sobre su experiencia y conocimientos.

El saludo debe ser en español, profesional pero cercano, y no más de 2-3 oraciones.

Responde solo con el texto del saludo, sin comillas ni formato adicional.
"""

INTERVIEW_QUESTION_PROMPT = """Eres un entrevistador profesional de recursos humanos.

Debes formular una pregunta clara y directa al candidato sobre el siguiente requisito que no se encontró en su CV:

REQUISITO: {requirement}

INSTRUCCIONES:
- La pregunta debe ser directa y fácil de entender.
- Pregunta si tiene experiencia o conocimientos en el tema.
- Sé amable y profesional.
- La pregunta debe ser en español.
- Responde SOLO con la pregunta, sin introducción ni formato adicional.
"""

EVALUATE_ANSWER_PROMPT = """Eres un experto en recursos humanos evaluando respuestas de candidatos.

REQUISITO EVALUADO: {requirement}

PREGUNTA REALIZADA: {question}

RESPUESTA DEL CANDIDATO: {answer}

INSTRUCCIONES:
Analiza si la respuesta del candidato indica que cumple el requisito.
- Si menciona experiencia, conocimientos o formación relacionada: CUMPLE
- Si dice que no tiene experiencia o conocimientos: NO CUMPLE
- Si la respuesta es ambigua o evasiva: NO CUMPLE

Responde ÚNICAMENTE con un JSON válido:
{{
    "fulfills_requirement": true o false,
    "reasoning": "Breve explicación"
}}
"""

GENERATE_FAREWELL_PROMPT = """Eres un entrevistador profesional de recursos humanos.

Genera un mensaje de despedida breve para el candidato, informándole de:
- Puntuación inicial (antes de la entrevista): {initial_score}%
- Puntuación final (después de la entrevista): {final_score}%
- Si fue descartado: {discarded}

INSTRUCCIONES:
- Sé amable y profesional.
- Si la puntuación mejoró, felicítale.
- Si fue descartado, sé empático pero profesional.
- Agradece su tiempo.
- El mensaje debe ser en español y no más de 3-4 oraciones.

Responde solo con el texto del mensaje, sin comillas ni formato adicional.
"""
