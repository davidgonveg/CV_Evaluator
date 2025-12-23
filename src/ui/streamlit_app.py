"""Interfaz de usuario Streamlit para CV Evaluator."""

import streamlit as st
from pathlib import Path

from src.config import settings
from src.services.llm_service import LLMService
from src.services.cv_analyzer import CVAnalyzer
from src.services.interviewer import Interviewer


def init_session_state():
    """Inicializa el estado de la sesión."""
    if "phase" not in st.session_state:
        st.session_state.phase = "input"  # input, analysis, interview, results
    if "cv_result" not in st.session_state:
        st.session_state.cv_result = None
    if "job_offer" not in st.session_state:
        st.session_state.job_offer = None
    if "final_result" not in st.session_state:
        st.session_state.final_result = None
    if "current_question_idx" not in st.session_state:
        st.session_state.current_question_idx = 0
    if "interview_responses" not in st.session_state:
        st.session_state.interview_responses = []
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "llm_service" not in st.session_state:
        st.session_state.llm_service = None
    if "interviewer" not in st.session_state:
        st.session_state.interviewer = None
    if "questions_generated" not in st.session_state:
        st.session_state.questions_generated = []
    if "newly_fulfilled" not in st.session_state:
        st.session_state.newly_fulfilled = []


def get_llm_service():
    """Obtiene o crea el servicio LLM."""
    if st.session_state.llm_service is None:
        st.session_state.llm_service = LLMService()
    return st.session_state.llm_service


def load_sample_data():
    """Carga datos de ejemplo."""
    data_dir = Path(__file__).parent.parent.parent / "data"

    offer_path = data_dir / "sample_offer.txt"
    cv_path = data_dir / "sample_cv.txt"

    offer_text = ""
    cv_text = ""

    if offer_path.exists():
        offer_text = offer_path.read_text(encoding="utf-8")
    if cv_path.exists():
        cv_text = cv_path.read_text(encoding="utf-8")

    return offer_text, cv_text


def render_input_phase():
    """Renderiza la fase de entrada de datos."""
    st.header("Fase 1: Entrada de datos")

    # Cargar datos de ejemplo
    sample_offer, sample_cv = load_sample_data()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Oferta de trabajo")
        offer_text = st.text_area(
            "Pega aquí los requisitos de la oferta",
            value=sample_offer,
            height=300,
            key="offer_input",
        )

    with col2:
        st.subheader("CV del candidato")
        cv_text = st.text_area(
            "Pega aquí el CV del candidato",
            value=sample_cv,
            height=300,
            key="cv_input",
        )

    if st.button("Analizar CV", type="primary", use_container_width=True):
        if not offer_text.strip() or not cv_text.strip():
            st.error("Por favor, introduce tanto la oferta como el CV")
            return

        with st.spinner("Analizando CV con IA..."):
            try:
                llm_service = get_llm_service()
                analyzer = CVAnalyzer(llm_service)
                cv_result, job_offer = analyzer.analyze(offer_text, cv_text)

                st.session_state.cv_result = cv_result
                st.session_state.job_offer = job_offer
                st.session_state.phase = "analysis"
                st.rerun()

            except Exception as e:
                st.error(f"Error al analizar: {str(e)}")
                st.info("Asegúrate de que Ollama está ejecutándose con el modelo configurado.")


def render_analysis_phase():
    """Renderiza los resultados del análisis inicial."""
    st.header("Resultado del análisis inicial")

    cv_result = st.session_state.cv_result

    # Mostrar puntuación
    col1, col2, col3 = st.columns(3)

    with col1:
        score_color = "normal" if not cv_result.discarded else "off"
        st.metric(
            "Puntuación",
            f"{cv_result.score}%",
            delta=None if not cv_result.discarded else "Descartado",
            delta_color=score_color,
        )

    with col2:
        st.metric(
            "Requisitos cumplidos",
            len(cv_result.matching_requirements),
        )

    with col3:
        st.metric(
            "Requisitos no encontrados",
            len(cv_result.not_found_requirements),
        )

    # Estado de descarte
    if cv_result.discarded:
        st.error(f"Candidato DESCARTADO por no cumplir requisito obligatorio: {cv_result.discarding_requirement}")
    else:
        st.success("Candidato NO descartado")

    # Detalles
    st.subheader("Detalles de la evaluación")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Requisitos cumplidos:**")
        if cv_result.matching_requirements:
            for req in cv_result.matching_requirements:
                st.markdown(f"- {req}")
        else:
            st.markdown("_Ninguno_")

    with col2:
        st.markdown("**Requisitos no encontrados en CV:**")
        if cv_result.not_found_requirements:
            for req in cv_result.not_found_requirements:
                st.markdown(f"- {req}")
        else:
            st.markdown("_Ninguno_")

    if cv_result.unmatching_requirements:
        st.markdown("**Requisitos no cumplidos:**")
        for req in cv_result.unmatching_requirements:
            st.markdown(f"- {req}")

    # JSON resultado
    with st.expander("Ver JSON completo"):
        st.json(cv_result.model_dump())

    # Botones de acción
    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Volver al inicio", use_container_width=True):
            st.session_state.phase = "input"
            st.session_state.cv_result = None
            st.session_state.job_offer = None
            st.rerun()

    with col2:
        if not cv_result.discarded and cv_result.not_found_requirements:
            if st.button("Iniciar entrevista", type="primary", use_container_width=True):
                st.session_state.phase = "interview"
                st.session_state.current_question_idx = 0
                st.session_state.interview_responses = []
                st.session_state.messages = []
                st.session_state.questions_generated = []
                st.session_state.newly_fulfilled = []

                # Crear interviewer
                llm_service = get_llm_service()
                st.session_state.interviewer = Interviewer(llm_service)

                st.rerun()
        elif cv_result.discarded:
            st.info("No se puede entrevistar: candidato descartado")
        else:
            st.info("No hay requisitos pendientes de verificar")


def render_interview_phase():
    """Renderiza la fase de entrevista."""
    st.header("Fase 2: Entrevista")

    cv_result = st.session_state.cv_result
    interviewer = st.session_state.interviewer
    not_found = cv_result.not_found_requirements
    current_idx = st.session_state.current_question_idx

    # Progreso
    total_questions = len(not_found)
    st.progress(current_idx / total_questions if total_questions > 0 else 1.0)
    st.caption(f"Pregunta {min(current_idx + 1, total_questions)} de {total_questions}")

    # Chat container
    chat_container = st.container()

    with chat_container:
        # Mostrar historial de mensajes
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    # Generar saludo inicial si es necesario
    if not st.session_state.messages:
        with st.spinner("Generando saludo..."):
            greeting = interviewer.generate_greeting()
            st.session_state.messages.append({
                "role": "assistant",
                "content": greeting
            })
            st.rerun()

    # Generar pregunta si es necesario
    if current_idx < total_questions:
        if len(st.session_state.questions_generated) <= current_idx:
            with st.spinner("Generando pregunta..."):
                question = interviewer.generate_question(not_found[current_idx])
                st.session_state.questions_generated.append(question)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": question
                })
                st.rerun()

    # Input del candidato
    if current_idx < total_questions:
        if answer := st.chat_input("Tu respuesta..."):
            # Añadir respuesta al chat
            st.session_state.messages.append({
                "role": "user",
                "content": answer
            })

            # Evaluar respuesta
            with st.spinner("Evaluando respuesta..."):
                requirement = not_found[current_idx]
                question = st.session_state.questions_generated[current_idx]

                response = interviewer.evaluate_answer(requirement, question, answer)
                st.session_state.interview_responses.append(response)

                if response.fulfills_requirement:
                    st.session_state.newly_fulfilled.append(requirement)

            # Siguiente pregunta
            st.session_state.current_question_idx += 1

            # Si terminamos, ir a resultados
            if st.session_state.current_question_idx >= total_questions:
                st.session_state.phase = "results"

            st.rerun()
    else:
        # Ya terminamos las preguntas
        st.session_state.phase = "results"
        st.rerun()


def render_results_phase():
    """Renderiza los resultados finales."""
    st.header("Resultados finales")

    cv_result = st.session_state.cv_result
    job_offer = st.session_state.job_offer
    interviewer = st.session_state.interviewer
    newly_fulfilled = st.session_state.newly_fulfilled

    # Calcular puntuación final
    total_requirements = len(job_offer.requirements)
    initial_fulfilled = len(cv_result.matching_requirements)
    final_fulfilled = initial_fulfilled + len(newly_fulfilled)

    initial_score = cv_result.score
    if cv_result.discarded:
        final_score = 0
    elif total_requirements > 0:
        final_score = int((final_fulfilled / total_requirements) * 100)
    else:
        final_score = 100

    # Métricas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Puntuación inicial",
            f"{initial_score}%",
        )

    with col2:
        delta = final_score - initial_score
        st.metric(
            "Puntuación final",
            f"{final_score}%",
            delta=f"+{delta}%" if delta > 0 else None,
        )

    with col3:
        st.metric(
            "Requisitos totales cumplidos",
            f"{final_fulfilled}/{total_requirements}",
        )

    # Mensaje de despedida
    st.divider()
    with st.spinner("Generando mensaje de despedida..."):
        farewell = interviewer.generate_farewell(initial_score, final_score, cv_result.discarded)
        st.info(farewell)

    # Detalle de respuestas
    st.subheader("Detalle de la entrevista")

    for i, response in enumerate(st.session_state.interview_responses, 1):
        with st.expander(f"Pregunta {i}: {response.requirement}"):
            st.markdown(f"**Pregunta:** {response.question}")
            st.markdown(f"**Respuesta:** {response.answer}")
            if response.fulfills_requirement:
                st.success("Requisito cumplido")
            else:
                st.warning("Requisito no cumplido")

    # Resumen final
    st.subheader("Resumen de requisitos")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Requisitos cumplidos:**")
        all_fulfilled = cv_result.matching_requirements + newly_fulfilled
        for req in all_fulfilled:
            st.markdown(f"- {req}")

    with col2:
        st.markdown("**Requisitos no cumplidos:**")
        not_fulfilled = [
            req for req in cv_result.not_found_requirements
            if req not in newly_fulfilled
        ] + cv_result.unmatching_requirements
        if not_fulfilled:
            for req in not_fulfilled:
                st.markdown(f"- {req}")
        else:
            st.markdown("_Ninguno_")

    # Botón reiniciar
    st.divider()
    if st.button("Nueva evaluación", type="primary", use_container_width=True):
        # Reset state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


def main():
    """Punto de entrada principal de la aplicación Streamlit."""
    st.set_page_config(
        page_title="CV Evaluator",
        page_icon="📝",
        layout="wide",
    )

    st.title("CV Evaluator - Sistema de Evaluación de Candidatos")
    st.caption(f"Usando: {settings.llm_provider.value} / {settings.llm_model}")

    init_session_state()

    # Verificar conexión con LLM
    with st.sidebar:
        st.header("Configuración")
        st.write(f"**Proveedor:** {settings.llm_provider.value}")
        st.write(f"**Modelo:** {settings.llm_model}")

        if st.button("Verificar conexión"):
            with st.spinner("Verificando..."):
                try:
                    llm = get_llm_service()
                    if llm.health_check():
                        st.success("Conexión OK")
                    else:
                        st.error("Error de conexión")
                except Exception as e:
                    st.error(f"Error: {e}")

        st.divider()
        st.markdown("""
        **Instrucciones:**
        1. Introduce la oferta de trabajo
        2. Introduce el CV del candidato
        3. Analiza para obtener puntuación inicial
        4. Si hay requisitos no encontrados, inicia la entrevista
        5. Responde las preguntas del entrevistador
        6. Obtén la puntuación final
        """)

    # Renderizar fase actual
    if st.session_state.phase == "input":
        render_input_phase()
    elif st.session_state.phase == "analysis":
        render_analysis_phase()
    elif st.session_state.phase == "interview":
        render_interview_phase()
    elif st.session_state.phase == "results":
        render_results_phase()


if __name__ == "__main__":
    main()
