"""Schemas Pydantic para validación de datos."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RequirementType(str, Enum):
    """Tipo de requisito de la oferta."""

    MANDATORY = "mandatory"  # Obligatorio - descarta si no se cumple
    OPTIONAL = "optional"    # Opcional/Deseable - suma puntos pero no descarta


class Requirement(BaseModel):
    """Modelo para un requisito de la oferta de trabajo."""

    description: str = Field(..., description="Descripción del requisito")
    requirement_type: RequirementType = Field(
        ..., description="Tipo de requisito (obligatorio u opcional)"
    )

    model_config = ConfigDict(use_enum_values=True)


class JobOffer(BaseModel):
    """Modelo para una oferta de trabajo con sus requisitos."""

    title: Optional[str] = Field(None, description="Título del puesto")
    requirements: List[Requirement] = Field(
        default_factory=list, description="Lista de requisitos"
    )


class CVEvaluationResult(BaseModel):
    """Resultado de la evaluación inicial del CV."""

    score: int = Field(..., ge=0, le=100, description="Puntuación del 0 al 100")
    discarded: bool = Field(
        ..., description="Si el candidato ha sido descartado por requisito obligatorio"
    )
    matching_requirements: List[str] = Field(
        default_factory=list, description="Requisitos cumplidos"
    )
    unmatching_requirements: List[str] = Field(
        default_factory=list, description="Requisitos obligatorios no cumplidos"
    )
    not_found_requirements: List[str] = Field(
        default_factory=list, description="Requisitos no encontrados en el CV"
    )
    discarding_requirement: Optional[str] = Field(
        None, description="Requisito obligatorio que causó el descarte"
    )


class InterviewResponse(BaseModel):
    """Respuesta del candidato a una pregunta de la entrevista."""

    requirement: str = Field(..., description="Requisito sobre el que se preguntó")
    question: str = Field(..., description="Pregunta realizada")
    answer: str = Field(..., description="Respuesta del candidato")
    fulfills_requirement: bool = Field(
        ..., description="Si la respuesta cumple el requisito"
    )


class FinalEvaluationResult(BaseModel):
    """Resultado final tras la entrevista."""

    initial_score: int = Field(..., description="Puntuación inicial del CV")
    final_score: int = Field(..., description="Puntuación final tras entrevista")
    discarded: bool = Field(..., description="Si el candidato fue descartado")
    total_requirements: int = Field(..., description="Total de requisitos")
    fulfilled_requirements: int = Field(..., description="Requisitos cumplidos")
    matching_requirements: List[str] = Field(
        default_factory=list, description="Todos los requisitos cumplidos"
    )
    unmatching_requirements: List[str] = Field(
        default_factory=list, description="Requisitos no cumplidos"
    )
    interview_responses: List[InterviewResponse] = Field(
        default_factory=list, description="Respuestas de la entrevista"
    )
