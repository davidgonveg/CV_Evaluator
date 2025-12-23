"""Servicio de entrevista - Fase 2 del sistema."""

from typing import List, Generator, Tuple

from src.models.schemas import (
    CVEvaluationResult,
    InterviewResponse,
    FinalEvaluationResult,
    JobOffer,
)
from src.prompts.templates import (
    INTERVIEW_QUESTION_PROMPT,
    EVALUATE_ANSWER_PROMPT,
    GENERATE_GREETING_PROMPT,
    GENERATE_FAREWELL_PROMPT,
)
from src.services.llm_service import LLMService


class Interviewer:
    """Entrevistador virtual para la fase 2 del sistema."""

    def __init__(self, llm_service: LLMService):
        """
        Inicializa el entrevistador.

        Args:
            llm_service: Servicio LLM para las interacciones
        """
        self.llm = llm_service
        self.interview_responses: List[InterviewResponse] = []

    def generate_greeting(self) -> str:
        """Genera un saludo inicial para el candidato."""
        return self.llm.invoke(GENERATE_GREETING_PROMPT)

    def generate_question(self, requirement: str) -> str:
        """
        Genera una pregunta sobre un requisito específico.

        Args:
            requirement: Requisito sobre el que preguntar

        Returns:
            Pregunta formulada
        """
        return self.llm.invoke_with_template(
            INTERVIEW_QUESTION_PROMPT,
            {"requirement": requirement}
        )

    def evaluate_answer(
        self, requirement: str, question: str, answer: str
    ) -> InterviewResponse:
        """
        Evalúa la respuesta del candidato a una pregunta.

        Args:
            requirement: Requisito evaluado
            question: Pregunta realizada
            answer: Respuesta del candidato

        Returns:
            InterviewResponse con el resultado
        """
        response = self.llm.invoke_with_template_json(
            EVALUATE_ANSWER_PROMPT,
            {
                "requirement": requirement,
                "question": question,
                "answer": answer,
            }
        )

        interview_response = InterviewResponse(
            requirement=requirement,
            question=question,
            answer=answer,
            fulfills_requirement=response.get("fulfills_requirement", False),
        )

        self.interview_responses.append(interview_response)
        return interview_response

    def generate_farewell(
        self, initial_score: int, final_score: int, discarded: bool
    ) -> str:
        """
        Genera un mensaje de despedida con los resultados.

        Args:
            initial_score: Puntuación inicial
            final_score: Puntuación final
            discarded: Si fue descartado

        Returns:
            Mensaje de despedida
        """
        return self.llm.invoke_with_template(
            GENERATE_FAREWELL_PROMPT,
            {
                "initial_score": initial_score,
                "final_score": final_score,
                "discarded": "Sí" if discarded else "No",
            }
        )

    def conduct_interview(
        self, cv_result: CVEvaluationResult, job_offer: JobOffer
    ) -> Generator[Tuple[str, str], str, FinalEvaluationResult]:
        """
        Conduce la entrevista completa como un generador.

        Este es un generador que:
        1. Yield: (tipo_mensaje, mensaje) - para mostrar al candidato
        2. Recibe: respuesta del candidato via send()
        3. Return: FinalEvaluationResult al terminar

        Args:
            cv_result: Resultado de la evaluación inicial
            job_offer: Oferta con los requisitos

        Yields:
            Tuplas (tipo, mensaje) donde tipo es 'greeting', 'question', o 'farewell'

        Returns:
            Resultado final de la evaluación
        """
        self.interview_responses = []

        # Saludo inicial
        greeting = self.generate_greeting()
        yield ("greeting", greeting)

        # Preguntas sobre requisitos no encontrados
        requirements_to_ask = cv_result.not_found_requirements.copy()
        newly_fulfilled = []

        for requirement in requirements_to_ask:
            question = self.generate_question(requirement)
            answer = yield ("question", question)

            if answer:
                response = self.evaluate_answer(requirement, question, answer)
                if response.fulfills_requirement:
                    newly_fulfilled.append(requirement)

        # Calcular puntuación final
        total_requirements = len(job_offer.requirements)
        initial_fulfilled = len(cv_result.matching_requirements)
        final_fulfilled = initial_fulfilled + len(newly_fulfilled)

        if cv_result.discarded:
            final_score = 0
        elif total_requirements > 0:
            final_score = int((final_fulfilled / total_requirements) * 100)
        else:
            final_score = 100

        # Actualizar listas de requisitos
        final_matching = cv_result.matching_requirements + newly_fulfilled
        final_unmatching = [
            req for req in requirements_to_ask if req not in newly_fulfilled
        ] + cv_result.unmatching_requirements

        # Mensaje de despedida
        farewell = self.generate_farewell(
            cv_result.score, final_score, cv_result.discarded
        )
        yield ("farewell", farewell)

        return FinalEvaluationResult(
            initial_score=cv_result.score,
            final_score=final_score,
            discarded=cv_result.discarded,
            total_requirements=total_requirements,
            fulfilled_requirements=final_fulfilled,
            matching_requirements=final_matching,
            unmatching_requirements=final_unmatching,
            interview_responses=self.interview_responses,
        )

    def run_interview_simple(
        self,
        cv_result: CVEvaluationResult,
        job_offer: JobOffer,
        get_answer_callback,
    ) -> FinalEvaluationResult:
        """
        Ejecuta la entrevista de forma simple con callback.

        Args:
            cv_result: Resultado de evaluación inicial
            job_offer: Oferta de trabajo
            get_answer_callback: Función que recibe pregunta y retorna respuesta

        Returns:
            Resultado final
        """
        self.interview_responses = []
        newly_fulfilled = []

        for requirement in cv_result.not_found_requirements:
            question = self.generate_question(requirement)
            answer = get_answer_callback(question)

            if answer:
                response = self.evaluate_answer(requirement, question, answer)
                if response.fulfills_requirement:
                    newly_fulfilled.append(requirement)

        # Calcular puntuación final
        total_requirements = len(job_offer.requirements)
        initial_fulfilled = len(cv_result.matching_requirements)
        final_fulfilled = initial_fulfilled + len(newly_fulfilled)

        if cv_result.discarded:
            final_score = 0
        elif total_requirements > 0:
            final_score = int((final_fulfilled / total_requirements) * 100)
        else:
            final_score = 100

        final_matching = cv_result.matching_requirements + newly_fulfilled
        final_unmatching = [
            req for req in cv_result.not_found_requirements
            if req not in newly_fulfilled
        ] + cv_result.unmatching_requirements

        return FinalEvaluationResult(
            initial_score=cv_result.score,
            final_score=final_score,
            discarded=cv_result.discarded,
            total_requirements=total_requirements,
            fulfilled_requirements=final_fulfilled,
            matching_requirements=final_matching,
            unmatching_requirements=final_unmatching,
            interview_responses=self.interview_responses,
        )
