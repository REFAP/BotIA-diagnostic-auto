#!/usr/bin/env python3
"""
Script de test d'intégration BotIA
Vérifie que tout fonctionne correctement après installation

Usage: python scripts/test_integration.py
"""

import sys
import os
import json
from pathlib import Path

# Ajouter le répertoire parent au path pour importer le moteur
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_database_files():
    """Test de présence et validité des fichiers de base de données"""
    print("🔍 Test des fichiers de base de données...")
    
    # Chemins à vérifier
    database_files = [
        "données/diagnostics_complet.json",
        "données/diagnostics.json"  # Fichier original
    ]
    
    results = []
    
    for db_file in database_files:
        if os.path.exists(db_file):
            try:
                with open(db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                diagnostics_count = len(data.get('diagnostics', {}))
                version = data.get('version', 'N/A')
                
                results.append({
                    'file': db_file,
                    'status': 'OK',
                    'diagnostics': diagnostics_count,
                    'version': version
                })
                print(f"  ✅ {db_file}: {diagnostics_count} diagnostics (v{version})")
                
            except json.JSONDecodeError as e:
                results.append({
                    'file': db_file,
                    'status': 'ERROR',
                    'error': f'JSON invalide: {e}'
                })
                print(f"  ❌ {db_file}: Erreur JSON - {e}")
        else:
            results.append({
                'file': db_file,
                'status': 'MISSING'
            })
            print(f"  ⚠️ {db_file}: Fichier manquant")
    
    return results

def test_engine_import():
    """Test d'importation du moteur de diagnostic"""
    print("\n🐍 Test d'importation du moteur...")
    
    try:
        from js.diagnostic_engine import BotIADiagnosticEngine
        print("  ✅ Importation réussie")
        return True
    except ImportError as e:
        print(f"  ❌ Erreur d'importation: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Erreur inattendue: {e}")
        return False

def test_engine_functionality():
    """Test des fonctionnalités du moteur"""
    print("\n⚙️ Test des fonctionnalités du moteur...")
    
    try:
        from js.diagnostic_engine import BotIADiagnosticEngine
        
        # Initialisation
        engine = BotIADiagnosticEngine()
        print("  ✅ Initialisation réussie")
        
        # Tests de diagnostic
        test_cases = [
            "voyant moteur allumé",
            "freins qui grincent", 
            "problème de batterie",
            "ma voiture surchauffe"
        ]
        
        success_count = 0
        total_tests = len(test_cases)
        
        for test_input in test_cases:
            try:
                result = engine.diagnose(test_input, top_n=2)
                
                if result['top_matches']:
                    top_match = result['top_matches'][0]
                    score = top_match['score']
                    title = top_match['titre']
                    
                    if score > 0.3:  # Seuil de qualité acceptable
                        print(f"  ✅ '{test_input}' → {title} (score: {score:.3f})")
                        success_count += 1
                    else:
                        print(f"  ⚠️ '{test_input}' → {title} (score faible: {score:.3f})")
                else:
                    print(f"  ❌ '{test_input}' → Aucun résultat")
                    
            except Exception as e:
                print(f"  ❌ '{test_input}' → Erreur: {e}")
        
        success_rate = (success_count / total_tests) * 100
        print(f"\n  📊 Taux de réussite: {success_count}/{total_tests} ({success_rate:.1f}%)")
        
        return success_rate >= 75  # Au moins 75% de réussite
        
    except Exception as e:
        print(f"  ❌ Erreur lors du test: {e}")
        return False

def test_output_format():
    """Test du formatage de sortie"""
    print("\n📄 Test du formatage de sortie...")
    
    try:
        from js.diagnostic_engine import BotIADiagnosticEngine
        
        engine = BotIADiagnosticEngine()
        result = engine.diagnose("voyant moteur", top_n=1)
        
        # Test formatage
        formatted = engine.format_response(result)
        
        # Vérifications basiques
        checks = [
            ("Présence du titre", "BotIA" in formatted),
            ("Présence du diagnostic", len(formatted) > 100),
            ("Formatage markdown", "**" in formatted),
            ("Icônes", any(emoji in formatted for emoji in ["🔧", "⚠️", "🚨", "ℹ️"]))
        ]
        
        all_passed = True
        for check_name, check_result in checks:
            if check_result:
                print(f"  ✅ {check_name}")
            else:
                print(f"  ❌ {check_name}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"  ❌ Erreur lors du test de formatage: {e}")
        return False

def test_performance():
    """Test de performance basique"""
    print("\n⚡ Test de performance...")
    
    try:
        import time
        from js.diagnostic_engine import BotIADiagnosticEngine
        
        engine = BotIADiagnosticEngine()
        
        # Test de 10 requêtes
        test_queries = ["voyant moteur"] * 10
        
        start_time = time.time()
        
        for query in test_queries:
            engine.diagnose(query, top_n=3)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / len(test_queries)
        
        print(f"  📊 {len(test_queries)} requêtes en {total_time:.3f}s")
        print(f"  📊 Temps moyen: {avg_time*1000:.1f}ms par requête")
        
        # Performance acceptable si < 100ms par requête
        performance_ok = avg_time < 0.1
        
        if performance_ok:
            print("  ✅ Performance acceptable")
        else:
            print("  ⚠️ Performance lente")
        
        return performance_ok
        
    except Exception as e:
        print(f"  ❌ Erreur lors du test de performance: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🧪 BotIA - Tests d'Intégration")
    print("=" * 50)
    
    # Exécution des tests
    tests = [
        ("Base de données", test_database_files),
        ("Importation moteur", test_engine_import),
        ("Fonctionnalités", test_engine_functionality),
        ("Formatage sortie", test_output_format),
        ("Performance", test_performance)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            if test_name == "Base de données":
                # Cas spécial pour le test de base de données
                db_results = test_func()
                # Considérer comme réussi si au moins un fichier DB existe
                success = any(r.get('status') == 'OK' for r in db_results)
            else:
                success = test_func()
            
            results[test_name] = success
            
        except Exception as e:
            print(f"\n❌ Erreur inattendue dans {test_name}: {e}")
            results[test_name] = False
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for success in results.values() if success)
    
    for test_name, success in results.items():
        status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
        print(f"{status:12} {test_name}")
    
    print("-" * 50)
    success_rate = (passed_tests / total_tests) * 100
    print(f"Résultats: {passed_tests}/{total_tests} tests réussis ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("\n🎉 BotIA est prêt à l'emploi !")
        exit_code = 0
    elif success_rate >= 60:
        print("\n⚠️ BotIA fonctionne mais nécessite des améliorations")
        exit_code = 1
    else:
        print("\n❌ BotIA nécessite une configuration")
        exit_code = 2
    
    print("\n💡 Conseils:")
    if not results.get("Base de données", False):
        print("   • Vérifiez que diagnostics_complet.json existe dans données/")
    if not results.get("Importation moteur", False):
        print("   • Vérifiez que diagnostic_engine.py existe dans js/")
    if not results.get("Performance", False):
        print("   • Performance lente détectée, vérifiez la configuration")
    
    print(f"\n👥 Pour obtenir de l'aide: https://github.com/REFAP/BotIA-diagnostic-auto/issues")
    
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
