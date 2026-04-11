# Taches contextualisation Assemblee

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

## Tests

- [x] Tester les enums et la validation de sortie.
- [x] Tester le context builder sur des interventions enrichies.
- [x] Tester le provider mock.
- [x] Tester les decisions minimales du reviewer.

## Run pilote mock

- [x] Lancer une revue agentique mock du fichier pilote.
- [x] Produire `contextual_reviews_pilot.jsonl`.
- [x] Verifier le nombre de sorties produites.

## Remis a plus tard

- [ ] Brancher un provider LLM reel.
- [ ] Ecrire le prompt final.
- [ ] Ajouter une interface de revue humaine.
- [ ] Reinjecter la revue agentique dans D3.
