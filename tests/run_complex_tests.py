import sys
import json
import os
from pathlib import Path

# Add src to python path
sys.path.append(str(Path(__file__).parent.parent))

from src.services.llm_service import LLMService
from src.services.cv_analyzer import CVAnalyzer

def run_tests():
    print("Iniciando batería de tests complejos...")
    
    # Load data
    data_path = Path(__file__).parent / "test_data" / "complex_cases.json"
    with open(data_path, "r", encoding="utf-8") as f:
        cases = json.load(f)
    
    # Init service
    try:
        llm_service = LLMService()
        if not llm_service.health_check():
            print("ERROR: Ollama no responde. Asegúrate de que está corriendo.")
            return
        analyzer = CVAnalyzer(llm_service)
    except Exception as e:
        print(f"Error inicializando servicios: {e}")
        return

    results = []
    
    print(f"\nEjecutando {len(cases)} casos de prueba...\n")
    
    for case in cases:
        print(f"Testing: {case['id']} - {case['description']}...")
        
        cv_result, _ = analyzer.analyze(case['offer'], case['cv'])
        
        # Validate expectations
        expected = case['expected']
        
        failures = []
        
        # Check matching count
        if 'matching_count' in expected:
            if len(cv_result.matching_requirements) != expected['matching_count']:
                failures.append(f"Matching count mismatch: Expected {expected['matching_count']}, got {len(cv_result.matching_requirements)} ({cv_result.matching_requirements})")
        
        # Check unmatching count
        if 'unmatching_count' in expected:
            if len(cv_result.unmatching_requirements) != expected['unmatching_count']:
                failures.append(f"Unmatching count mismatch: Expected {expected['unmatching_count']}, got {len(cv_result.unmatching_requirements)} ({cv_result.unmatching_requirements})")
                
         # Check not found count
        if 'not_found_count' in expected:
            if len(cv_result.not_found_requirements) != expected['not_found_count']:
                failures.append(f"Not found count mismatch: Expected {expected['not_found_count']}, got {len(cv_result.not_found_requirements)} ({cv_result.not_found_requirements})")

        # Check discarded
        if cv_result.discarded != expected['discarded']:
            failures.append(f"Discarded mismatch: Expected {expected['discarded']}, got {cv_result.discarded} (Reason: {cv_result.discarding_requirement})")

        # Store result
        res = {
            "id": case['id'],
            "passed": len(failures) == 0,
            "failures": failures,
            "raw_result": cv_result.model_dump()
        }
        results.append(res)
        
        if res['passed']:
            print("  PASSED ✅")
        else:
            print("  FAILED ❌")
            for fail in failures:
                print(f"    - {fail}")
            
            print("\n  🔍 Razonamiento del LLM:")
            # Imprimir razonamiento si está disponible (depende de si se actualizó el modelo)
            if hasattr(cv_result, 'evaluations_with_reasoning'):
                for eval_item in cv_result.evaluations_with_reasoning:
                    print(f"    - [{eval_item.status.upper()}] {eval_item.requirement}")
                    print(f"      Explain: {eval_item.reasoning}")

        print("-" * 40)

    # Summary
    passed_count = sum(1 for r in results if r['passed'])
    print(f"\nResumen: {passed_count}/{len(cases)} tests pasados.")
    
    # Save detailed results for inspection
    debug_file = Path("tests/test_results_debug.json")
    with open(debug_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Resultados detallados guardados en: {debug_file}")
    
    if passed_count < len(cases):
        print("\nRecomendación: Revisa el archivo de debug para ver por qué falló el LLM.")
    else:
        print("\n¡Todos los tests pasaron! El prompt es robusto.")

if __name__ == "__main__":
    run_tests()
