#!/usr/bin/env python3
"""
Script de testing para el evaluador de CV.

Ejecuta múltiples casos de prueba y genera un informe JSON con los resultados.

Uso:
    python tests/test_evaluator.py           # Ejecutar todos los tests (requiere LLM)
    python tests/test_evaluator.py --dry-run # Solo probar separación de requisitos (sin LLM)

Salida:
    tests/test_results.json
"""

import json
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))


# =============================================================================
# CASOS DE PRUEBA
# =============================================================================

TEST_CASES = [
    # -------------------------------------------------------------------------
    # CASO 1: Candidato perfecto - cumple todo
    # -------------------------------------------------------------------------
    {
        "name": "Candidato perfecto",
        "description": "Candidato que cumple todos los requisitos obligatorios y opcionales",
        "offer": """
OFERTA: Desarrollador Python Senior

Requisitos:
- Experiencia mínima de 3 años en Python (obligatorio)
- Formación: Grado en Informática o similar (obligatorio)
- Valorable conocimientos en FastAPI y LangChain
""",
        "cv": """
CURRICULUM VITAE - Ana García

EXPERIENCIA:
- Desarrollador Senior en TechCorp (2019-2024) - 5 años
  Python, FastAPI, LangChain, desarrollo de APIs REST

FORMACIÓN:
- Grado en Ingeniería Informática - Universidad Politécnica (2015-2019)

HABILIDADES:
- Python (experto)
- FastAPI (avanzado)
- LangChain (intermedio)
- Docker, Git
""",
        "expected": {
            "discarded": False,
            "score_range": [75, 100],
            "should_match": ["Python", "Informática", "FastAPI", "LangChain"],
        }
    },

    # -------------------------------------------------------------------------
    # CASO 2: Descartado por falta de experiencia obligatoria
    # -------------------------------------------------------------------------
    {
        "name": "Sin experiencia suficiente",
        "description": "Candidato junior sin los 3 años requeridos - debe ser descartado",
        "offer": """
OFERTA: Desarrollador Python Senior

Requisitos:
- Experiencia mínima de 3 años en Python (obligatorio)
- Formación: Grado en Informática (obligatorio)
- Valorable Docker y Kubernetes
""",
        "cv": """
CURRICULUM VITAE - Juan Pérez

EXPERIENCIA:
- Becario en StartupX (2023-2024) - 1 año
  Desarrollo web con Python y Django

FORMACIÓN:
- Grado en Ingeniería Informática - UNED (2019-2023)

HABILIDADES:
- Python (intermedio)
- Django
- Git
""",
        "expected": {
            "discarded": True,
            "score_range": [0, 0],
            "reason": "experiencia mínima"
        }
    },

    # -------------------------------------------------------------------------
    # CASO 3: Cumple obligatorios pero NO opcionales
    # -------------------------------------------------------------------------
    {
        "name": "Solo requisitos obligatorios",
        "description": "Cumple lo obligatorio pero ningún opcional",
        "offer": """
OFERTA: Desarrollador Backend

Requisitos:
- Mínimo 2 años de experiencia en desarrollo backend (obligatorio)
- Título universitario en informática (obligatorio)
- Valorable experiencia en AWS
- Valorable conocimientos en Terraform
- Valorable certificación en cloud
""",
        "cv": """
CURRICULUM VITAE - María López

EXPERIENCIA:
- Desarrollador Backend en Empresa ABC (2020-2024) - 4 años
  Desarrollo de APIs en Java y Python

FORMACIÓN:
- Ingeniería Informática - Universidad de Sevilla (2016-2020)

HABILIDADES:
- Java, Python
- PostgreSQL, MySQL
- Git, Docker
""",
        "expected": {
            "discarded": False,
            "score_range": [30, 50],
            "should_match": ["experiencia", "informática"],
            "should_not_match": ["AWS", "Terraform", "cloud"]
        }
    },

    # -------------------------------------------------------------------------
    # CASO 4: Requisito compuesto - cumple parcialmente
    # -------------------------------------------------------------------------
    {
        "name": "Requisito compuesto parcial",
        "description": "Sabe FastAPI pero NO LangChain - debe recibir crédito parcial",
        "offer": """
OFERTA: Desarrollador IA

Requisitos:
- Experiencia mínima de 2 años en Python (obligatorio)
- Grado universitario (obligatorio)
- Valorable conocimientos en FastAPI y LangChain
""",
        "cv": """
CURRICULUM VITAE - Carlos Ruiz

EXPERIENCIA:
- Desarrollador Python en DataCorp (2020-2024) - 4 años
  Desarrollo de APIs con FastAPI, servicios REST

FORMACIÓN:
- Grado en Ingeniería Informática - UPM (2016-2020)

HABILIDADES:
- Python (avanzado)
- FastAPI (avanzado)
- Machine Learning básico
- NO tiene experiencia con LangChain
""",
        "expected": {
            "discarded": False,
            "score_range": [60, 85],
            "should_match": ["Python", "FastAPI"],
            "should_not_match": ["LangChain"]
        }
    },

    # -------------------------------------------------------------------------
    # CASO 5: Múltiples tecnologías opcionales
    # -------------------------------------------------------------------------
    {
        "name": "Lista larga de opcionales",
        "description": "Oferta con muchos requisitos opcionales, candidato cumple algunos",
        "offer": """
OFERTA: Full Stack Developer

Requisitos obligatorios:
- Mínimo 3 años de experiencia en desarrollo web

Requisitos valorables:
- Conocimientos en React, Angular o Vue
- Experiencia con Node.js y Express
- Manejo de MongoDB y PostgreSQL
- Docker y Kubernetes
- CI/CD con Jenkins o GitLab
""",
        "cv": """
CURRICULUM VITAE - Laura Sánchez

EXPERIENCIA:
- Full Stack Developer en WebAgency (2018-2024) - 6 años
  React, Node.js, MongoDB

FORMACIÓN:
- Ciclo Superior DAW

HABILIDADES:
- React (experto)
- Node.js (avanzado)
- Express (avanzado)
- MongoDB (avanzado)
- Docker (intermedio)
- Git
""",
        "expected": {
            "discarded": False,
            "score_range": [50, 80],
            "should_match": ["React", "Node.js", "MongoDB", "Docker"],
            "should_not_match": ["Kubernetes", "PostgreSQL", "Jenkins", "GitLab"]
        }
    },

    # -------------------------------------------------------------------------
    # CASO 6: Sin formación requerida
    # -------------------------------------------------------------------------
    {
        "name": "Sin formación universitaria",
        "description": "Tiene experiencia pero no el título requerido - debe ser descartado",
        "offer": """
OFERTA: Data Scientist

Requisitos:
- Imprescindible Máster o Doctorado en IA/ML/Estadística
- Experiencia mínima de 2 años en Data Science
- Valorable Python y R
""",
        "cv": """
CURRICULUM VITAE - Pedro Martín

EXPERIENCIA:
- Data Scientist en Analytics Inc (2019-2024) - 5 años
  Machine Learning, Deep Learning, Python, TensorFlow

FORMACIÓN:
- Bootcamp de Data Science - IronHack (2019)
- Bachillerato científico

HABILIDADES:
- Python (experto)
- R (intermedio)
- TensorFlow, PyTorch
- SQL
""",
        "expected": {
            "discarded": True,
            "score_range": [0, 0],
            "reason": "formación"
        }
    },

    # -------------------------------------------------------------------------
    # CASO 7: Alternativas en formación (OR)
    # -------------------------------------------------------------------------
    {
        "name": "Formación alternativa (OR)",
        "description": "Tiene Master en IA (alternativa válida a Grado en Informática)",
        "offer": """
OFERTA: ML Engineer

Requisitos:
- Formación requerida: Grado en Informática o Máster en IA
- Mínimo 2 años en Machine Learning
- Valorable experiencia con PyTorch y TensorFlow
""",
        "cv": """
CURRICULUM VITAE - Elena García

EXPERIENCIA:
- ML Engineer en AILabs (2021-2024) - 3 años
  Desarrollo de modelos de ML, PyTorch, MLOps

FORMACIÓN:
- Máster en Inteligencia Artificial - Universidad Carlos III (2020-2021)
- Grado en Matemáticas - UCM (2016-2020)

HABILIDADES:
- Python, PyTorch (experto)
- TensorFlow (intermedio)
- MLOps, Docker
""",
        "expected": {
            "discarded": False,
            "score_range": [70, 100],
            "should_match": ["Máster", "Machine Learning", "PyTorch", "TensorFlow"]
        }
    },

    # -------------------------------------------------------------------------
    # CASO 8: CV vacío de habilidades relevantes
    # -------------------------------------------------------------------------
    {
        "name": "CV sin match",
        "description": "CV de un perfil completamente diferente",
        "offer": """
OFERTA: DevOps Engineer

Requisitos:
- Experiencia mínima de 3 años en DevOps
- Conocimientos obligatorios en AWS o Azure
- Valorable Terraform y Ansible
- Valorable Kubernetes
""",
        "cv": """
CURRICULUM VITAE - Roberto Fernández

EXPERIENCIA:
- Diseñador Gráfico en Agencia Creativa (2015-2024) - 9 años
  Diseño de logos, branding, Photoshop, Illustrator

FORMACIÓN:
- Grado en Bellas Artes - Universidad de Valencia

HABILIDADES:
- Adobe Photoshop (experto)
- Adobe Illustrator (experto)
- Figma
- HTML/CSS básico
""",
        "expected": {
            "discarded": True,
            "score_range": [0, 0],
            "reason": "DevOps"
        }
    },
]


# =============================================================================
# FUNCIONES DE TESTING
# =============================================================================

def run_single_test(analyzer, test_case: dict) -> dict:
    """Ejecuta un único caso de prueba."""
    print(f"\n{'='*60}")
    print(f"📋 TEST: {test_case['name']}")
    print(f"   {test_case['description']}")
    print('='*60)

    try:
        # Ejecutar análisis
        result, job_offer = analyzer.analyze(
            offer_text=test_case['offer'],
            cv_text=test_case['cv']
        )

        # Preparar resultado
        test_result = {
            "name": test_case["name"],
            "description": test_case["description"],
            "status": "SUCCESS",
            "requirements_parsed": [
                {
                    "description": req.description,
                    "type": req.requirement_type.value
                }
                for req in job_offer.requirements
            ],
            "evaluation": {
                "score": result.score,
                "discarded": result.discarded,
                "discarding_requirement": result.discarding_requirement,
                "matching_requirements": result.matching_requirements,
                "unmatching_requirements": result.unmatching_requirements,
                "not_found_requirements": result.not_found_requirements,
            },
            "expected": test_case["expected"],
            "validation": {}
        }

        # Validar resultados
        expected = test_case["expected"]

        # Validar descarte
        if "discarded" in expected:
            test_result["validation"]["discarded_match"] = (
                result.discarded == expected["discarded"]
            )

        # Validar rango de score
        if "score_range" in expected:
            min_score, max_score = expected["score_range"]
            test_result["validation"]["score_in_range"] = (
                min_score <= result.score <= max_score
            )

        # Mostrar resultados
        print(f"\n📊 RESULTADOS:")
        print(f"   Score: {result.score}%")
        print(f"   Descartado: {'❌ SÍ' if result.discarded else '✅ NO'}")
        if result.discarding_requirement:
            print(f"   Motivo descarte: {result.discarding_requirement}")

        print(f"\n   ✅ Requisitos cumplidos ({len(result.matching_requirements)}):")
        for req in result.matching_requirements:
            print(f"      - {req}")

        print(f"\n   ❌ Requisitos no cumplidos ({len(result.unmatching_requirements)}):")
        for req in result.unmatching_requirements:
            print(f"      - {req}")

        print(f"\n   ❓ No encontrados ({len(result.not_found_requirements)}):")
        for req in result.not_found_requirements:
            print(f"      - {req}")

        # Mostrar requisitos parseados (para verificar separación)
        print(f"\n   📝 Requisitos parseados ({len(job_offer.requirements)}):")
        for req in job_offer.requirements:
            tipo = "🔴 OBL" if req.requirement_type.value == "mandatory" else "🟢 OPT"
            print(f"      {tipo} {req.description}")

        return test_result

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return {
            "name": test_case["name"],
            "description": test_case["description"],
            "status": "ERROR",
            "error": str(e),
            "expected": test_case["expected"],
        }


def run_all_tests():
    """Ejecuta todos los casos de prueba."""
    print("\n" + "="*70)
    print("🧪 INICIANDO SUITE DE TESTS - CV EVALUATOR")
    print("="*70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total de casos: {len(TEST_CASES)}")

    # Inicializar servicios
    try:
        llm_service = LLMService()
        analyzer = CVAnalyzer(llm_service)
        print(f"LLM Provider: {llm_service.provider}")
        print(f"LLM Model: {llm_service.model}")
    except Exception as e:
        print(f"\n❌ Error inicializando LLM: {e}")
        print("Asegúrate de que Ollama está corriendo o configura otro provider.")
        sys.exit(1)

    # Ejecutar tests
    results = {
        "timestamp": datetime.now().isoformat(),
        "llm_provider": str(llm_service.provider),
        "llm_model": llm_service.model,
        "total_tests": len(TEST_CASES),
        "tests": []
    }

    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}]", end="")
        test_result = run_single_test(analyzer, test_case)
        results["tests"].append(test_result)

    # Resumen
    print("\n" + "="*70)
    print("📊 RESUMEN DE RESULTADOS")
    print("="*70)

    success = sum(1 for t in results["tests"] if t["status"] == "SUCCESS")
    errors = sum(1 for t in results["tests"] if t["status"] == "ERROR")

    print(f"✅ Exitosos: {success}/{len(TEST_CASES)}")
    print(f"❌ Errores: {errors}/{len(TEST_CASES)}")

    # Validaciones
    validations_passed = 0
    validations_total = 0
    for test in results["tests"]:
        if "validation" in test:
            for key, passed in test["validation"].items():
                validations_total += 1
                if passed:
                    validations_passed += 1

    if validations_total > 0:
        print(f"✓ Validaciones: {validations_passed}/{validations_total}")

    # Guardar resultados
    output_path = Path(__file__).parent / "test_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Resultados guardados en: {output_path}")

    return results


def run_dry_run():
    """
    Modo dry-run: prueba solo la lógica de separación de requisitos.
    No requiere LLM ni dependencias externas.
    """
    import re
    from typing import List
    from enum import Enum

    # Copiar las funciones de separación para no depender de imports
    def _split_list_items(text: str, include_or: bool = True) -> List[str]:
        text = re.sub(r',\s*y\s+', ', ', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+y\s+', ', ', text, flags=re.IGNORECASE)
        if include_or:
            text = re.sub(r',\s*o\s+', ', ', text, flags=re.IGNORECASE)
            parts = re.split(r'\s+o\s+', text, flags=re.IGNORECASE)
            if len(parts) > 1 and all(len(p.split()) <= 2 for p in parts):
                text = ', '.join(parts)
        items = [item.strip() for item in text.split(',')]
        items = [item for item in items if item]
        return items

    def _split_compound_requirement(description: str) -> List[str]:
        prefixes = [
            r"conocimientos?\s+(?:en|de|sobre)",
            r"experiencia\s+(?:en|con)",
            r"manejo\s+de",
            r"dominio\s+de",
            r"uso\s+de",
            r"trabajo\s+con",
        ]
        prefix_match = None
        for prefix in prefixes:
            match = re.search(prefix, description, re.IGNORECASE)
            if match:
                prefix_match = match
                break
        if prefix_match:
            before_prefix = description[:prefix_match.start()]
            prefix_text = description[prefix_match.start():prefix_match.end()]
            after_prefix = description[prefix_match.end():].strip()
            items = _split_list_items(after_prefix)
            if len(items) > 1:
                return [f"{before_prefix}{prefix_text} {item.strip()}" for item in items]
        simple_split = _split_list_items(description)
        if len(simple_split) > 1:
            if all(len(item.split()) <= 3 for item in simple_split):
                return simple_split
        return [description]

    # Tipos simples para el dry-run
    class RequirementType(str, Enum):
        MANDATORY = "mandatory"
        OPTIONAL = "optional"

    class Requirement:
        def __init__(self, description: str, requirement_type: RequirementType):
            self.description = description
            self.requirement_type = requirement_type

    def _expand_compound_requirements(requirements):
        expanded = []
        for req in requirements:
            split_descriptions = _split_compound_requirement(req.description)
            for desc in split_descriptions:
                expanded.append(Requirement(
                    description=desc,
                    requirement_type=req.requirement_type
                ))
        return expanded

    print("\n" + "="*70)
    print("🧪 DRY-RUN: Test de separación de requisitos (sin LLM)")
    print("="*70)

    # Casos de prueba para separación
    separation_tests = [
        {
            "input": "Valorable conocimientos en FastAPI y LangChain",
            "expected_count": 2,
            "expected_contains": ["FastAPI", "LangChain"]
        },
        {
            "input": "Experiencia en Python, Java y Go",
            "expected_count": 3,
            "expected_contains": ["Python", "Java", "Go"]
        },
        {
            "input": "Manejo de Docker y Kubernetes",
            "expected_count": 2,
            "expected_contains": ["Docker", "Kubernetes"]
        },
        {
            "input": "Experiencia mínima de 3 años en Python",
            "expected_count": 1,
            "expected_contains": ["Python"]
        },
        {
            "input": "Formación: Grado en Informática o Máster en IA",
            "expected_count": 1,  # NO debe separar alternativas de formación
            "expected_contains": ["Grado", "Máster"]
        },
        {
            "input": "Dominio de React, Angular o Vue",
            "expected_count": 3,
            "expected_contains": ["React", "Angular", "Vue"]
        },
        {
            "input": "Conocimientos en AWS y Azure y GCP",
            "expected_count": 3,
            "expected_contains": ["AWS", "Azure", "GCP"]
        },
    ]

    results = []
    passed = 0

    for test in separation_tests:
        result = _split_compound_requirement(test["input"])
        count_ok = len(result) == test["expected_count"]
        contains_ok = all(
            any(exp.lower() in r.lower() for r in result)
            for exp in test["expected_contains"]
        )
        test_passed = count_ok and contains_ok

        if test_passed:
            passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"

        print(f"\n{status} Input: \"{test['input']}\"")
        print(f"   Esperado: {test['expected_count']} items")
        print(f"   Obtenido: {len(result)} items")
        for r in result:
            print(f"      → \"{r}\"")

        results.append({
            "input": test["input"],
            "output": result,
            "expected_count": test["expected_count"],
            "actual_count": len(result),
            "passed": test_passed
        })

    print("\n" + "="*70)
    print(f"📊 RESUMEN: {passed}/{len(separation_tests)} tests pasados")
    print("="*70)

    # También probar con los casos de TEST_CASES
    print("\n" + "="*70)
    print("📝 Requisitos que se extraerían de cada oferta:")
    print("="*70)

    for test_case in TEST_CASES:
        print(f"\n🔹 {test_case['name']}")

        # Simular extracción de requisitos (solo buscar líneas con "-")
        lines = test_case["offer"].split("\n")
        mock_requirements = []
        for line in lines:
            line = line.strip()
            if line.startswith("-"):
                req_text = line[1:].strip()
                # Detectar tipo
                lower = req_text.lower()
                if any(kw in lower for kw in ["obligatorio", "mínimo", "imprescindible", "requerido"]):
                    req_type = RequirementType.MANDATORY
                else:
                    req_type = RequirementType.OPTIONAL

                mock_requirements.append(Requirement(
                    description=req_text,
                    requirement_type=req_type
                ))

        # Expandir
        expanded = _expand_compound_requirements(mock_requirements)

        print(f"   Original: {len(mock_requirements)} requisitos")
        print(f"   Expandido: {len(expanded)} requisitos")
        for req in expanded:
            tipo = "🔴" if req.requirement_type == RequirementType.MANDATORY else "🟢"
            print(f"      {tipo} {req.description}")

    # Guardar resultados
    output_path = Path(__file__).parent / "dry_run_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "mode": "dry-run",
            "separation_tests": results,
            "passed": passed,
            "total": len(separation_tests)
        }, f, indent=2, ensure_ascii=False)

    print(f"\n📁 Resultados guardados en: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tests para CV Evaluator")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo probar separación de requisitos (no requiere LLM)"
    )
    args = parser.parse_args()

    if args.dry_run:
        run_dry_run()
    else:
        from src.services.cv_analyzer import CVAnalyzer
        from src.services.llm_service import LLMService
        run_all_tests()
