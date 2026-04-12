# Taches contextualisation Assemblee

Note : cette checklist retrace le pilote v0/v1. Le contrat metier cible v2
est documente dans
[`docs/assemblee_contextualization_contract_v2.md`](assemblee_contextualization_contract_v2.md).
Le planning actif est desormais suivi dans
[`docs/assemblee_roadmap.md`](assemblee_roadmap.md).

## Documentation

- [x] Documenter l'objectif de la brique.
- [x] Documenter sa place dans le workflow.
- [x] Documenter ce que la brique fait.
- [x] Documenter ce que la brique ne fait pas.
- [x] Documenter les contrats d'entree et de sortie.
- [x] Documenter les enums autorisees.
- [x] Documenter les regles de combinaison decision / revue humaine.

## Squelette

- [x] Creer le package `src/assemblee_contextualization`.
- [x] Definir les enums strictes.
- [x] Definir les dataclasses de contrat.
- [x] Construire un payload de contexte depuis les interventions enrichies.
- [x] Definir une interface provider-agnostic.
- [x] Ajouter un provider mock stable.
- [x] Ajouter un reviewer minimal.
- [x] Valider la sortie du provider.
- [x] Ajouter un provider Mistral reel de test.
- [x] Conserver le provider mock.
- [x] Ajouter un runner pilote configurable.

## Tests

- [x] Tester les enums et la validation de sortie.
- [x] Tester le context builder sur des interventions enrichies.
- [x] Tester le provider mock.
- [x] Tester les decisions minimales du reviewer.
- [x] Tester le provider Mistral sans appel reseau.
- [x] Tester le fallback si cle API absente.
- [x] Tester le fallback si la reponse Mistral est invalide.
- [x] Tester la validation minimale du payload Mistral.

## Run pilote mock

- [x] Lancer une revue agentique mock du fichier pilote.
- [x] Produire `contextual_reviews_pilot.jsonl`.
- [x] Verifier le nombre de sorties produites.

## Run pilote Mistral

- [x] Documenter les variables `MISTRAL_API_KEY` et `MISTRAL_MODEL`.
- [x] Ajouter `.env.example` sans secret.
- [x] Ajouter le chargement local de `.env`.
- [x] Lancer le runner pilote avec le provider Mistral.
- [x] Produire `contextual_reviews_pilot.jsonl` au format JSONL.
- [x] Verifier le nombre de sorties produites.

## Remis a plus tard

- [ ] Ecrire le prompt final.
- [ ] Ajouter une interface de revue humaine.
- [ ] Reinjecter la revue agentique dans D3.
