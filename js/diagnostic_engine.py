#!/usr/bin/env python3
"""
BotIA - Moteur de Diagnostic Automobile Intelligent
Compatible avec la base de données GitHub REFAP/BotIA-diagnostic-auto

Usage:
    python js/diagnostic_engine.py "voyant moteur allumé"
    python js/diagnostic_engine.py --interactive
"""

import json
import os
import sys
import argparse
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

# Configuration
URGENCY_SCORE = {"critique": 9, "elevee": 7, "moyenne": 4, "faible": 1}
URGENCY_ICONS = {"critique": "🚨", "elevee": "⚠️", "moyenne": "🔧", "faible": "ℹ️"}

class BotIADiagnosticEngine:
    """
    Moteur de diagnostic automobile intelligent pour BotIA
    """
    
    def __init__(self, database_path=None):
        """Initialise le moteur avec la base de données"""
        
        # Détection automatique du chemin de la base
        if database_path is None:
            # Essai des chemins possibles
            possible_paths = [
                "données/diagnostics_complet.json",
                "données/diagnostics.json", 
                "data/diagnostics.json",
                "../données/diagnostics_complet.json"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    database_path = path
                    break
            
            if database_path is None:
                raise FileNotFoundError("❌ Aucune base de données trouvée. Vérifiez les chemins.")
        
        self.database_path = database_path
        self.data = None
        self.load_database()
    
    def load_database(self):
        """Charge la base de données depuis le fichier JSON"""
        try:
            with open(self.database_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            diagnostics_count = len(self.data.get('diagnostics', {}))
            print(f"✅ Base BotIA chargée: {diagnostics_count} diagnostics disponibles")
            
            # Affichage des métadonnées si disponibles
            if 'metadata' in self.data:
                meta = self.data['metadata']
                print(f"📊 Métadonnées: {meta.get('total_keywords', 'N/A')} mots-clés, version {self.data.get('version', 'N/A')}")
            
        except FileNotFoundError:
            raise Exception(f"❌ Base de données non trouvée: {self.database_path}")
        except json.JSONDecodeError as e:
            raise Exception(f"❌ Erreur de format JSON: {e}")
    
    def normalize_text(self, text):
        """Normalise le texte (supprime accents, met en minuscules)"""
        text = text.lower()
        text = unicodedata.normalize('NFD', text)
        text = ''.join(ch for ch in text if unicodedata.category(ch) != 'Mn')
        return text.strip()
    
    def fuzzy_similarity(self, a, b):
        """Calcule la similarité entre deux chaînes"""
        return SequenceMatcher(None, a, b).ratio()
    
    def compute_match_score(self, user_input, diagnostic):
        """Calcule le score de correspondance entre l'input utilisateur et un diagnostic"""
        
        input_norm = self.normalize_text(user_input)
        input_tokens = set(input_norm.split())
        
        best_keyword = None
        exact_match = 0
        token_overlap = 0
        fuzzy_best = 0
        partial_matches = 0
        
        keywords = diagnostic.get('keywords', [])
        
        for keyword in keywords:
            kw_norm = self.normalize_text(keyword)
            kw_tokens = set(kw_norm.split())
            
            # 1. Correspondance exacte (keyword complet dans l'input)
            if kw_norm in input_norm:
                exact_match = 1.0
                best_keyword = keyword
                break
            
            # 2. Correspondance partielle (keyword dans l'input)
            if any(kw_word in input_norm for kw_word in kw_tokens):
                partial_matches += 1
                if best_keyword is None:
                    best_keyword = keyword
            
            # 3. Overlap de tokens
            intersection = input_tokens.intersection(kw_tokens)
            union = input_tokens.union(kw_tokens)
            
            if union:
                overlap_ratio = len(intersection) / len(union)
                token_overlap = max(token_overlap, overlap_ratio)
            
            # 4. Similarité fuzzy
            fuzzy_score = self.fuzzy_similarity(input_norm, kw_norm)
            if fuzzy_score > fuzzy_best:
                fuzzy_best = fuzzy_score
                if best_keyword is None and fuzzy_score > 0.6:
                    best_keyword = keyword
        
        # Calcul du score composite
        urgency_score = URGENCY_SCORE.get(diagnostic.get('urgence', 'faible'), 1)
        confidence = 0.7 if diagnostic.get('contributeur') == 'système' else 0.85
        
        # Pondération des différents critères
        score = (
            0.4 * exact_match +                    # Correspondance exacte (priorité max)
            0.2 * min(partial_matches / len(keywords), 1.0) +  # Correspondances partielles
            0.2 * token_overlap +                  # Overlap de mots
            0.1 * (urgency_score / 10) +          # Boost selon urgence
            0.1 * fuzzy_best                      # Similarité fuzzy
        )
        
        return {
            'score': round(score, 3),
            'matched_keyword': best_keyword,
            'exact_match': exact_match > 0,
            'partial_matches': partial_matches,
            'token_overlap': round(token_overlap, 3),
            'fuzzy': round(fuzzy_best, 3)
        }
    
    def diagnose(self, user_input, top_n=3):
        """
        Fonction principale de diagnostic
        
        Args:
            user_input (str): Description du problème par l'utilisateur
            top_n (int): Nombre de résultats à retourner
            
        Returns:
            dict: Résultats du diagnostic avec scores et suggestions
        """
        
        if not self.data or not self.data.get('diagnostics'):
            raise Exception("❌ Base de données non chargée ou vide")
        
        results = []
        diagnostics = self.data['diagnostics']
        
        # Calcul des scores pour chaque diagnostic
        for diag_id, diag_data in diagnostics.items():
            match_info = self.compute_match_score(user_input, diag_data)
            
            if match_info['score'] > 0.1:  # Seuil minimum de pertinence
                results.append({
                    'id': diag_id,
                    'titre': diag_data['titre'],
                    'score': match_info['score'],
                    'urgence': diag_data['urgence'],
                    'urgence_score': URGENCY_SCORE.get(diag_data['urgence'], 1),
                    'matched_keyword': match_info['matched_keyword'],
                    'causes': diag_data.get('causes', []),
                    'solutions': diag_data.get('solutions', []),
                    'cout_estime': diag_data.get('cout_estime', 'N/A'),
                    'contributeur': diag_data.get('contributeur', 'inconnu'),
                    'details': match_info
                })
        
        # Tri par score décroissant, puis par urgence
        results.sort(key=lambda x: (x['score'], x['urgence_score']), reverse=True)
        
        # Détection d'ambiguïté
        clarification = None
        if len(results) >= 2:
            delta_score = results[0]['score'] - results[1]['score']
            if delta_score < 0.15 and results[0]['score'] > 0.4:
                clarification = (
                    f"🤔 Symptômes ambigus entre '{results[0]['titre']}' et '{results[1]['titre']}'. "
                    f"Pouvez-vous préciser : s'agit-il plutôt de {results[0]['titre'].lower()} "
                    f"ou de {results[1]['titre'].lower()} ?"
                )
        
        return {
            'input': user_input,
            'total_matches': len(results),
            'top_matches': results[:top_n],
            'clarification': clarification,
            'confidence': results[0]['score'] if results else 0,
            'database_version': self.data.get('version', 'inconnue')
        }
    
    def format_response(self, diagnosis_result):
        """Formate la réponse de diagnostic de façon lisible"""
        
        if not diagnosis_result['top_matches']:
            return f"❓ Désolé, aucun diagnostic trouvé pour : '{diagnosis_result['input']}'\n💡 Essayez avec d'autres mots-clés ou soyez plus spécifique."
        
        response = []
        response.append(f"🤖 **BotIA - Diagnostic pour :** '{diagnosis_result['input']}'")
        response.append(f"📊 **Confiance :** {diagnosis_result['confidence']:.1%} | **Correspondances :** {diagnosis_result['total_matches']}")
        response.append("")
        
        for i, result in enumerate(diagnosis_result['top_matches'], 1):
            icon = URGENCY_ICONS.get(result['urgence'], '🔧')
            
            response.append(f"**{i}. {icon} {result['titre']}**")
            response.append(f"   📈 Score: {result['score']:.3f} | 🚨 Urgence: {result['urgence']} | 🔍 Mot-clé: '{result['matched_keyword']}'")
            response.append(f"   💰 Coût estimé: {result['cout_estime']}")
            
            # Causes principales (max 3)
            if result['causes']:
                response.append("   🧩 **Causes possibles:**")
                for cause in result['causes'][:3]:
                    response.append(f"      • {cause}")
            
            # Solutions prioritaires (max 3)
            if result['solutions']:
                response.append("   🔧 **Solutions recommandées:**")
                for solution in result['solutions'][:3]:
                    # Highlighting des solutions urgentes
                    if any(urgent in solution.lower() for urgent in ['arrêt', 'immédiat', 'urgence']):
                        response.append(f"      🚨 {solution}")
                    else:
                        response.append(f"      • {solution}")
            
            response.append("")
        
        # Clarification si nécessaire
        if diagnosis_result['clarification']:
            response.append(f"💬 **Besoin de clarification:**")
            response.append(f"   {diagnosis_result['clarification']}")
            response.append("")
        
        # Statistiques de debug (optionnel)
        if diagnosis_result['top_matches']:
            best = diagnosis_result['top_matches'][0]
            details = best['details']
            response.append(f"🔍 **Détails matching:** Exact={details['exact_match']}, Partiels={details['partial_matches']}, Tokens={details['token_overlap']}, Fuzzy={details['fuzzy']}")
        
        return "\n".join(response)

def main():
    """Fonction principale avec interface en ligne de commande"""
    
    parser = argparse.ArgumentParser(description='BotIA - Moteur de Diagnostic Automobile')
    parser.add_argument('query', nargs='?', help='Description du problème automobile')
    parser.add_argument('--interactive', '-i', action='store_true', help='Mode interactif')
    parser.add_argument('--database', '-d', help='Chemin vers la base de données JSON')
    parser.add_argument('--top', '-t', type=int, default=3, help='Nombre de résultats (défaut: 3)')
    parser.add_argument('--debug', action='store_true', help='Mode debug avec détails')
    
    args = parser.parse_args()
    
    try:
        # Initialisation du moteur
        print("🚗 BotIA - Assistant de Diagnostic Automobile")
        print("=" * 50)
        
        engine = BotIADiagnosticEngine(args.database)
        
        if args.interactive:
            # Mode interactif
            print("💬 Mode interactif - Décrivez votre problème automobile")
            print("(Tapez 'quit' pour quitter)")
            print("-" * 50)
            
            while True:
                try:
                    user_input = input("\n🚗 Votre problème: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        print("👋 Au revoir !")
                        break
                    
                    if not user_input:
                        continue
                    
                    # Diagnostic
                    result = engine.diagnose(user_input, args.top)
                    response = engine.format_response(result)
                    print("\n" + response)
                    
                except KeyboardInterrupt:
                    print("\n👋 Au revoir !")
                    break
        
        elif args.query:
            # Mode requête unique
            result = engine.diagnose(args.query, args.top)
            response = engine.format_response(result)
            print(response)
            
            if args.debug:
                print("\n🔧 DEBUG - Détails techniques:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
        
        else:
            # Aucune requête fournie, afficher l'aide
            parser.print_help()
            print("\n💡 Exemples d'utilisation:")
            print("  python js/diagnostic_engine.py \"voyant moteur allumé\"")
            print("  python js/diagnostic_engine.py \"freins qui grincent\" --top 5")
            print("  python js/diagnostic_engine.py --interactive")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
