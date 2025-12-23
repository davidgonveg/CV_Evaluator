"""Servicio de análisis de CV - Fase 1 del sistema."""

from typing import List

from src.models.schemas import (
    Requirement,
    RequirementType,
    JobOffer,
    CVEvaluationResult,
)
from src.prompts.templates import PARSE_OFFER_PROMPT, EVALUATE_CV_PROMPT
from src.services.llm_service import LLMService


class CVAnalyzer:
    """Analizador de CV contra requisitos de oferta de trabajo."""

    def __init__(self, llm_service: LLMService):
        """
        Inicializa el analizador de CV.

        Args:
            llm_service: Servicio LLM para las evaluaciones
        """
        self.llm = llm_service

    def parse_job_offer(self, offer_text: str) -> JobOffer:
        """
        Parsea una oferta de trabajo y extrae los requisitos.

        Args:
            offer_text: Texto de la oferta de trabajo

        Returns:
            JobOffer con los requisitos extraídos
        """
        response = self.llm.invoke_with_template_json(
            PARSE_OFFER_PROMPT,
            {"offer_text": offer_text}
        )

        requirements = []
        for req in response.get("requirements", []):
            req_type = req.get("requirement_type", "optional").lower()
            requirements.append(
                Requirement(
                    description=req["description"],
                    requirement_type=(
                        RequirementType.MANDATORY
                        if req_type == "mandatory"
                        else RequirementType.OPTIONAL
                    ),
                )
            )

        return JobOffer(requirements=requirements)

    def evaluate_cv(
        self, cv_text: str, job_offer: JobOffer
    ) -> CVEvaluationResult:
        """
        Evalúa un CV contra los requisitos de una oferta.

        Args:
            cv_text: Texto del CV del candidato
            job_offer: Oferta de trabajo con requisitos

        Returns:
            Resultado de la evaluación
        """
        # Preparar requisitos para el prompt
        requirements_json = [
            {
                "description": req.description,
                "requirement_type": req.requirement_type,
            }
            for req in job_offer.requirements
        ]

        # Obtener evaluación del LLM
        response = self.llm.invoke_with_template_json(
            EVALUATE_CV_PROMPT,
            {
                "requirements_json": str(requirements_json),
                "cv_text": cv_text,
            }
        )

        # Procesar resultados
        matching = []
        unmatching = []
        not_found = []
        discarded = False
        discarding_req = None

        # Crear mapa de tipos de requisitos
        req_types = {
            req.description: req.requirement_type
            for req in job_offer.requirements
        }

        for evaluation in response.get("evaluations", []):
            req_desc = evaluation["requirement"]
            status = evaluation["status"]
            req_type = evaluation.get("requirement_type", "optional")

            # Determinar si es obligatorio
            is_mandatory = req_type == "mandatory" or req_type == RequirementType.MANDATORY

            if status == "matching":
                matching.append(req_desc)
            elif status == "unmatching":
                unmatching.append(req_desc)
                # Si es obligatorio y no cumple, descartar
                if is_mandatory:
                    discarded = True
                    discarding_req = req_desc
            elif status == "not_found":
                not_found.append(req_desc)
                # not_found en obligatorio también descarta
                if is_mandatory:
                    discarded = True
                    discarding_req = req_desc

        # Calcular puntuación
        total_requirements = len(job_offer.requirements)
        fulfilled = len(matching)

        if discarded:
            score = 0
        elif total_requirements > 0:
            score = int((fulfilled / total_requirements) * 100)
        else:
            score = 100

        return CVEvaluationResult(
            score=score,
            discarded=discarded,
            matching_requirements=matching,
            unmatching_requirements=unmatching,
            not_found_requirements=not_found,
            discarding_requirement=discarding_req,
        )

    def analyze(self, offer_text: str, cv_text: str) -> CVEvaluationResult:
        """
        Ejecuta el análisis completo: parsea oferta y evalúa CV.

        Args:
            offer_text: Texto de la oferta de trabajo
            cv_text: Texto del CV del candidato

        Returns:
            Resultado de la evaluación
        """
        job_offer = self.parse_job_offer(offer_text)
        return self.evaluate_cv(cv_text, job_offer), job_offer
