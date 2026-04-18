# OBSERVATOIRE — Consignes agent codeur

## Contexte projet

Pipeline d'analyse de débats parlementaires (Assemblée nationale, corpus XML
Syceron). Détection de signaux liés à la haine, au racisme, à la xénophobie,
à la discrimination et au ciblage problématique de groupes du périmètre
discriminatoire. Contextualisation via LLM (Mistral).

Le projet ne doit pas devenir un observatoire général de la tension politique,
du conflit parlementaire ou du climat civique.

Source de vérité planning : `docs/assemblee_roadmap.md`.
Contrat V2 de référence : `docs/assemblee_contextualization_contract_v2.md`.
Audit architecture : `docs/audit_architecture.md`.

## Méthode de travail

Procéder par petites étapes incrémentales. Une action claire, un test de
validation, puis on passe à la suite. Pas de modifications massives d'un coup.

- Découper chaque tâche en sous-étapes atomiques.
- Chaque sous-étape doit être testable et réversible.
- Valider les tests avant de passer à la sous-étape suivante.
- Ne jamais modifier plus d'un module à la fois sans raison explicite.
- Committer logiquement : un commit = une étape fonctionnelle.
- En cas de doute, poser la question plutôt que deviner.

## Style de code Python

Ce projet est orienté backend / data pipeline. Pas de frontend Python.

- Python 3.12+.
- Typage strict exigé : annotations de type sur toutes les signatures de
  fonctions et méthodes (paramètres et retour). Utiliser `from __future__
  import annotations` en tête de chaque module.
- Imports absolus préférés pour les modules hors package
  (`from src.build_assemblee_pilot import ...`). Imports relatifs autorisés
  à l'intérieur du package `assemblee_contextualization`.
- Pas de classes inutiles : préférer les fonctions pures et les dataclasses
  `frozen=True`.
- Pas de dépendance nouvelle sans justification explicite.
- Pas de `print()` pour le logging — utiliser le module `logging` standard
  pour tout nouveau code. Le code existant utilise encore `print()` ; ne pas
  le convertir sauf si la tâche le demande.
- Pas de secrets en dur. Les clés API passent par `.env` et `env.py`.
- Respecter l'arborescence existante :
  - `src/` : code source, modules, CLI.
  - `src/assemblee_contextualization/` : package principal.
  - `data/raw/` : données sources brutes, modifiées uniquement par les modules
    d'acquisition contrôlée.
  - `data/interim/` : sorties intermédiaires (CSV, JSONL, JSON).
  - `data/exports/d3/` : sorties publiques pour visualisation.
  - `docs/` : documentation projet.
  - `tests/` : tests pytest, miroir de `src/`.

## Tests

- Framework : `pytest`, dossier `tests/`.
- Structure miroir : `tests/assemblee/` pour `src/build_assemblee_*.py`,
  `tests/assemblee_contextualization/` pour
  `src/assemblee_contextualization/`.
- Toute nouvelle fonction ou modification de fonction existante doit avoir un
  test associé.
- Interdiction de valider une étape sans que les tests associés ne passent.
- Les tests ne doivent jamais dépendre du filesystem réel, de l'API Mistral
  ou du réseau. Utiliser `tmp_path`, des fixtures et des mocks.
- Nommage : `test_<module>.py`, fonctions `test_<comportement_attendu>`.
- Lancer les tests : `python -m pytest tests/ -v` depuis la racine.

## Contrats et invariants à respecter

- Le contrat V2 (`contracts.py`) est la référence. Ne jamais modifier les
  enums `ScopeLevel`, `SignalCategory`, `Confidence` ni les combinaisons
  autorisées sans décision documentée dans la roadmap.
- `is_fallback = true` n'est autorisé que pour `hors_perimetre / ambiguous`
  avec `needs_human_review = true` et `confidence = low`.
- `is_fallback = true` est toujours exclu des métriques substantielles.
- `needs_human_review = false` est autorisé uniquement pour
  `hors_perimetre / no_signal / confidence = high`.
- Le code V1 (`Decision`, `reviewer.py`, `mock_provider.py`,
  `mistral_provider.py`, `run_pilot.py`) est conservé pour historique. Ne pas
  y toucher sauf demande explicite.

## Ton et format des réponses

- Réponses directes. Format : **Action → Code → Résultat**.
- Pas de blabla introductif, pas de reformulation inutile de la demande.
- Montrer le code modifié, le test ajouté, le résultat d'exécution.
- Si une étape échoue, montrer l'erreur exacte et la correction.

## Refactoring en cours (Phase G)

Priorités Phase G identifiées dans `docs/audit_architecture.md` et
`docs/examen_modules_contextualization.md` :

1. Créer `pyproject.toml` avec dépendances et config outils.
2. Extraire un module `paths.py` centralisant `ROOT_DIR`, `SOURCE_DIR`,
   `INTERIM_DIR`, `_display_path`, `_session_slug`, `_normalize_syceron_date`,
   `_as_int`.
3. Unifier le parsing des métadonnées XML entre acquisition et inventaire.
4. Scinder `run_pilot_v2.py` en moteur de revue, IO V2 et CLI mince.
5. Scinder `build_assemblee_pilot.py` (parsing XML, règles lexicales, chemins,
   CLI).
6. Marquer le code V1 comme déprécié.
7. Consolider la visualisation et la politique des exports avant l'audit de
   fond.

Ne pas anticiper ces refactorings dans une tâche qui ne les concerne pas.
Appliquer chaque refactoring comme une étape isolée avec ses propres tests.
