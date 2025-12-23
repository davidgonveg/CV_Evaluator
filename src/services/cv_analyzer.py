"""Servicio de análisis de CV - Fase 1 del sistema."""

import re
from typing import List

from src.models.schemas import (
    Requirement,
    RequirementType,
    JobOffer,
    CVEvaluationResult,
    RequirementEvaluation,
    EvaluationSummary,
)
from src.prompts.templates import PARSE_OFFER_PROMPT, EVALUATE_CV_PROMPT
from src.services.llm_service import LLMService


def _split_compound_requirement(description: str) -> List[str]:
    """
    Separa un requisito compuesto en requisitos individuales.

    Ejemplo:
        "Valorable conocimientos en FastAPI y LangChain"
        -> ["Valorable conocimientos en FastAPI", "Valorable conocimientos en LangChain"]

        "Experiencia en Python, Java y Go"
        -> ["Experiencia en Python", "Experiencia en Java", "Experiencia en Go"]

    Args:
        description: Descripción del requisito que puede contener múltiples items

    Returns:
        Lista de requisitos individuales
    """
    # Patrones comunes que indican múltiples tecnologías/habilidades
    # Buscar patrones como "en X, Y y Z" o "de X y Y" o simplemente "X, Y, Z"

    # Palabras que típicamente preceden a listas de tecnologías
    prefixes = [
        r"conocimientos?\s+(?:en|de|sobre)",
        r"experiencia\s+(?:en|con)",
        r"manejo\s+de",
        r"dominio\s+de",
        r"uso\s+de",
        r"trabajo\s+con",
    ]

    # Intentar encontrar un prefijo que preceda a la lista
    prefix_match = None
    prefix_pattern = None
    for prefix in prefixes:
        match = re.search(prefix, description, re.IGNORECASE)
        if match:
            prefix_match = match
            prefix_pattern = prefix
            break

    if prefix_match:
        # Hay un prefijo, extraer lo que viene después
        before_prefix = description[:prefix_match.start()]
        prefix_text = description[prefix_match.start():prefix_match.end()]
        after_prefix = description[prefix_match.end():].strip()

        # Separar por ", " y " y " / " o "
        # Primero normalizar: "A, B y C" -> ["A", "B", "C"]
        items = _split_list_items(after_prefix)

        if len(items) > 1:
            # Reconstruir cada requisito individual
            return [f"{before_prefix}{prefix_text} {item.strip()}" for item in items]

    # Si no hay prefijo reconocido, intentar separar de forma más simple
    # Solo si hay patrones claros como "X y Y" donde X e Y parecen tecnologías
    simple_split = _split_list_items(description)
    if len(simple_split) > 1:
        # Verificar que los items parecen ser tecnologías/habilidades individuales
        # (palabras cortas, sin verbos comunes)
        if all(len(item.split()) <= 3 for item in simple_split):
            return simple_split

    # No se pudo separar, devolver como está
    return [description]


def _split_list_items(text: str, include_or: bool = True) -> List[str]:
    """
    Separa una lista de items conectados por comas y 'y'.
    El 'o' solo se procesa si include_or=True y los items son cortos (tecnologías).

    Ejemplo:
        "FastAPI y LangChain" -> ["FastAPI", "LangChain"]
        "Python, Java y Go" -> ["Python", "Java", "Go"]
        "React o Vue" -> ["React", "Vue"] (solo si include_or=True)

    Nota: "o" típicamente indica alternativas (cualquiera vale), mientras que
    "y" indica que se requieren/valoran ambas. Por eso somos más conservadores con "o".
    """
    # Primero reemplazar ", y " por solo coma
    text = re.sub(r',\s*y\s+', ', ', text, flags=re.IGNORECASE)

    # Reemplazar " y " por coma
    text = re.sub(r'\s+y\s+', ', ', text, flags=re.IGNORECASE)

    # Solo procesar "o" si está habilitado y parece una lista de tecnologías cortas
    if include_or:
        text = re.sub(r',\s*o\s+', ', ', text, flags=re.IGNORECASE)
        # Solo reemplazar " o " si ambos lados son cortos (parecen tecnologías)
        parts = re.split(r'\s+o\s+', text, flags=re.IGNORECASE)
        if len(parts) > 1 and all(len(p.split()) <= 2 for p in parts):
            text = ', '.join(parts)

    # Ahora separar por comas
    items = [item.strip() for item in text.split(',')]
    items = [item for item in items if item]  # Eliminar vacíos

    return items


def _expand_compound_requirements(requirements: List[Requirement]) -> List[Requirement]:
    """
    Expande requisitos compuestos en requisitos individuales.

    Args:
        requirements: Lista de requisitos que pueden contener items compuestos

    Returns:
        Lista expandida de requisitos individuales
    """
    expanded = []
    for req in requirements:
        split_descriptions = _split_compound_requirement(req.description)
        for desc in split_descriptions:
            expanded.append(Requirement(
                description=desc,
                requirement_type=req.requirement_type
            ))
    return expanded


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

        # Expandir requisitos compuestos (ej: "FastAPI y LangChain" -> 2 requisitos)
        expanded_requirements = _expand_compound_requirements(requirements)

        return JobOffer(requirements=expanded_requirements)

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
        evaluations_with_reasoning = []

        # Contadores para score ponderado
        mandatory_total = 0
        mandatory_fulfilled = 0
        optional_total = 0
        optional_fulfilled = 0

        for evaluation in response.get("evaluations", []):
            req_desc = evaluation["requirement"]
            status = evaluation["status"]
            req_type = evaluation.get("requirement_type", "optional")
            reasoning = evaluation.get("reasoning", "Sin explicación disponible")

            # Guardar evaluación con reasoning
            evaluations_with_reasoning.append(RequirementEvaluation(
                requirement=req_desc,
                requirement_type=req_type,
                status=status,
                reasoning=reasoning
            ))

            # Determinar si es obligatorio
            is_mandatory = req_type == "mandatory" or req_type == RequirementType.MANDATORY

            # Contar por tipo
            if is_mandatory:
                mandatory_total += 1
            else:
                optional_total += 1

            if status == "matching":
                matching.append(req_desc)
                if is_mandatory:
                    mandatory_fulfilled += 1
                else:
                    optional_fulfilled += 1
            elif status == "unmatching":
                unmatching.append(req_desc)
                if is_mandatory:
                    discarded = True
                    discarding_req = req_desc
            elif status == "not_found":
                not_found.append(req_desc)
                if is_mandatory:
                    discarded = True
                    discarding_req = req_desc

        # Calcular puntuación (todos los requisitos pesan igual)
        total_requirements = mandatory_total + optional_total
        fulfilled = len(matching)

        if discarded:
            score = 0
        elif total_requirements > 0:
            score = int((fulfilled / total_requirements) * 100)
        else:
            score = 100

        # Generar resumen ejecutivo
        summary = self._generate_summary(
            score=score,
            discarded=discarded,
            matching=matching,
            unmatching=unmatching,
            not_found=not_found,
            discarding_req=discarding_req
        )

        # Desglose del score
        score_breakdown = {
            "total_requirements": total_requirements,
            "fulfilled": fulfilled,
            "mandatory": {
                "fulfilled": mandatory_fulfilled,
                "total": mandatory_total,
            },
            "optional": {
                "fulfilled": optional_fulfilled,
                "total": optional_total,
            }
        }

        return CVEvaluationResult(
            score=score,
            discarded=discarded,
            matching_requirements=matching,
            unmatching_requirements=unmatching,
            not_found_requirements=not_found,
            discarding_requirement=discarding_req,
            evaluations_with_reasoning=evaluations_with_reasoning,
            summary=summary,
            score_breakdown=score_breakdown,
        )

    def _generate_summary(
        self,
        score: int,
        discarded: bool,
        matching: list,
        unmatching: list,
        not_found: list,
        discarding_req: str
    ) -> EvaluationSummary:
        """Genera un resumen ejecutivo de la evaluación."""

        # Determinar estado
        if discarded:
            status = "NO APTO"
            recommendation = f"Descartado por no cumplir requisito obligatorio: {discarding_req}"
        elif score >= 80:
            status = "APTO"
            recommendation = "Candidato recomendado para continuar en el proceso."
        elif score >= 50:
            status = "REVISAR"
            recommendation = "Candidato con potencial, revisar gaps antes de decidir."
        else:
            status = "NO APTO"
            recommendation = "Candidato no cumple suficientes requisitos."

        # Extraer fortalezas (requisitos matching, simplificados)
        strengths = []
        for req in matching[:5]:  # Máximo 5
            # Simplificar el texto del requisito
            simplified = req.replace("Valorable ", "").replace("conocimientos en ", "")
            simplified = simplified.replace("Experiencia mínima de ", "").replace("experiencia en ", "")
            strengths.append(simplified)

        # Extraer gaps (requisitos no cumplidos)
        gaps = []
        for req in (unmatching + not_found)[:5]:  # Máximo 5
            simplified = req.replace("Valorable ", "").replace("conocimientos en ", "")
            simplified = simplified.replace("Experiencia mínima de ", "").replace("experiencia en ", "")
            gaps.append(simplified)

        return EvaluationSummary(
            status=status,
            strengths=strengths,
            gaps=gaps,
            recommendation=recommendation
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
