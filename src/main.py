"""Punto de entrada principal para ejecución por terminal."""

import sys
from pathlib import Path

from src.config import settings
from src.services.llm_service import LLMService
from src.services.cv_analyzer import CVAnalyzer
from src.services.interviewer import Interviewer


def print_header():
    """Imprime el encabezado de la aplicación."""
    print("\n" + "=" * 60)
    print("       CV EVALUATOR - Sistema de Evaluación de Candidatos")
    print("=" * 60)
    print(f"Proveedor LLM: {settings.llm_provider.value}")
    print(f"Modelo: {settings.llm_model}")
    print("=" * 60 + "\n")


def load_file(prompt: str) -> str:
    """Carga un archivo o permite entrada manual."""
    print(prompt)
    choice = input("¿Cargar desde archivo? (s/n): ").strip().lower()

    if choice == "s":
        file_path = input("Ruta del archivo: ").strip()
        try:
            return Path(file_path).read_text(encoding="utf-8")
        except Exception as e:
            print(f"Error al leer archivo: {e}")
            print("Introduce el texto manualmente:")
            return input_multiline()
    else:
        print("Introduce el texto (termina con línea vacía):")
        return input_multiline()


def input_multiline() -> str:
    """Lee entrada multilínea hasta línea vacía."""
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    return "\n".join(lines)


def print_result(cv_result):
    """Imprime el resultado de la evaluación."""
    print("\n" + "-" * 40)
    print("RESULTADO DEL ANÁLISIS INICIAL")
    print("-" * 40)

    print(f"\nPuntuación: {cv_result.score}%")
    print(f"Descartado: {'Sí' if cv_result.discarded else 'No'}")

    if cv_result.discarding_requirement:
        print(f"Motivo del descarte: {cv_result.discarding_requirement}")

    print("\nRequisitos cumplidos:")
    for req in cv_result.matching_requirements:
        print(f"  - {req}")

    if cv_result.unmatching_requirements:
        print("\nRequisitos no cumplidos:")
        for req in cv_result.unmatching_requirements:
            print(f"  - {req}")

    print("\nRequisitos no encontrados en CV:")
    for req in cv_result.not_found_requirements:
        print(f"  - {req}")

    print("-" * 40)


def run_interview(cv_result, job_offer, llm_service):
    """Ejecuta la fase de entrevista."""
    interviewer = Interviewer(llm_service)

    print("\n" + "=" * 60)
    print("       FASE 2: ENTREVISTA")
    print("=" * 60 + "\n")

    # Saludo
    greeting = interviewer.generate_greeting()
    print(f"Entrevistador: {greeting}\n")

    # Preguntas
    newly_fulfilled = []
    for requirement in cv_result.not_found_requirements:
        question = interviewer.generate_question(requirement)
        print(f"Entrevistador: {question}")
        answer = input("Tú: ").strip()

        response = interviewer.evaluate_answer(requirement, question, answer)
        if response.fulfills_requirement:
            newly_fulfilled.append(requirement)
            print("(Requisito cumplido)\n")
        else:
            print("(Requisito no cumplido)\n")

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

    # Despedida
    farewell = interviewer.generate_farewell(
        cv_result.score, final_score, cv_result.discarded
    )
    print(f"\nEntrevistador: {farewell}")

    # Resultado final
    print("\n" + "=" * 60)
    print("       RESULTADO FINAL")
    print("=" * 60)
    print(f"Puntuación inicial: {cv_result.score}%")
    print(f"Puntuación final: {final_score}%")
    print(f"Requisitos cumplidos: {final_fulfilled}/{total_requirements}")
    print("=" * 60 + "\n")


def main():
    """Función principal."""
    print_header()

    # Verificar conexión
    print("Verificando conexión con LLM...")
    try:
        llm_service = LLMService()
        if not llm_service.health_check():
            print("ERROR: No se pudo conectar con el LLM")
            print("Asegúrate de que Ollama está ejecutándose.")
            sys.exit(1)
        print("Conexión OK\n")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Cargar datos
    offer_text = load_file("\n[OFERTA DE TRABAJO]")
    cv_text = load_file("\n[CV DEL CANDIDATO]")

    # Análisis
    print("\nAnalizando CV...")
    analyzer = CVAnalyzer(llm_service)
    cv_result, job_offer = analyzer.analyze(offer_text, cv_text)

    print_result(cv_result)

    # Entrevista si aplica
    if not cv_result.discarded and cv_result.not_found_requirements:
        proceed = input("\n¿Iniciar entrevista? (s/n): ").strip().lower()
        if proceed == "s":
            run_interview(cv_result, job_offer, llm_service)
    elif cv_result.discarded:
        print("\nNo se puede realizar entrevista: candidato descartado.")
    else:
        print("\nNo hay requisitos pendientes de verificar.")

    print("¡Gracias por usar CV Evaluator!")


if __name__ == "__main__":
    main()
