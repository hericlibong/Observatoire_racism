# Examen module par module — assemblee_contextualization

Date : 18 avril 2026

---

## Carte des 18 modules (2 776 lignes)

| Module | LOC | Role | Statut |
|--------|-----|------|--------|
| contracts.py | 306 | Enums, dataclasses, validateurs V1+V2 | **Actif, critique** |
| providers.py | 11 | Interface abstraite `ContextualReviewProvider` | **Actif, sain** |
| context_builder.py | 102 | Construction du payload contextuel | **Actif, sain** |
| run_pilot_v2.py | 315 | Orchestre V2 + fonctions utilitaires partagees | **Actif, problematique** |
| run_incremental_session_v2.py | 339 | Traitement incremental avec manifest/journal | **Actif, le plus gros** |
| run_phase_c_lot_v2.py | 124 | Traitement par lot Phase C | **Actif** |
| processing_journal.py | 71 | Journal JSONL anti-doublons | **Actif, sain** |
| source_acquisition.py | 287 | Import ZIP/XML, hash, validation | **Actif, sain** |
| source_inventory.py | 194 | Inventaire local des seances | **Actif, doublons** |
| source_manifest.py | 249 | Manifest enrichi depuis ZIP | **Actif** |
| heatmap_export.py | 236 | Export heatmap pour D3 | **Actif** |
| mistral_provider_v2.py | 188 | Provider LLM Mistral V2 | **Actif** |
| mock_provider_v2.py | 35 | Provider mock V2 | **Actif** |
| env.py | 30 | Chargement `.env` artisanal | **Actif, minimal** |
| **reviewer.py** | 40 | Orchestrateur V1 | **Mort en production** |
| **mock_provider.py** | 28 | Provider mock V1 | **Mort en production** |
| **mistral_provider.py** | 166 | Provider LLM Mistral V1 | **Mort en production** |
| **run_pilot.py** | 53 | CLI pilote V1 | **Mort en production** |

---

## Diagnostic 1 — Code V1 mort (287 lignes, 4 fichiers)

**Fichiers concernes** : `reviewer.py`, `mock_provider.py`, `mistral_provider.py`, `run_pilot.py`

**Constat** : ces 4 modules ne sont plus utilises par aucun flux de production. Leur seule consommation :
- `run_pilot.py` importe les 3 autres (`reviewer`, `mock_provider`, `mistral_provider`)
- `run_pilot.py` n'est importe par **personne** (ni en src, ni en tests)
- `mock_provider.py` est importe par `test_mock_provider.py` et `test_reviewer_decisions.py`
- `mistral_provider.py` est importe par `test_mistral_provider.py`
- `reviewer.py` est importe par `run_pilot.py` et `test_reviewer_decisions.py`

**Verdict** : tout le pipeline V2 passe par `run_pilot_v2.py` qui utilise directement `context_builder` + les providers V2, sans passer par `ContextualReviewer`. Le code V1 forme un sous-arbre isole.

**Suggestion** :
- Deplacer les 4 fichiers dans `src/assemblee_contextualization/legacy/` avec un `__init__.py` marque `# DEPRECATED — V1 conserve pour historique`
- Deplacer les tests associes dans `tests/assemblee_contextualization/legacy/`
- Les imports anciens cassent proprement, signalant la depreciation

---

## Diagnostic 2 — `run_pilot_v2.py` est un "God module" (315 lignes, 12 fonctions publiques)

Ce fichier cumule **5 responsabilites distinctes** :

| Responsabilite | Fonctions |
|---------------|-----------|
| **Orchestration review V2** | `review_candidates_v2()`, `select_review_ids()`, `sample_intervention_ids()`, `validate_fallback_invariants()` |
| **I/O lecture/ecriture JSONL** | `write_outputs_v2()`, `read_outputs_v2()` |
| **Resume et comparaison** | `summarize_outputs_v2()`, `summarize_output_file()`, `write_comparison_summary()` |
| **Chargement XML source** | `load_interventions_for_source()` (re-implemente le parsing XML de `build_assemblee_pilot`) |
| **Factory provider + CLI** | `build_provider()`, `default_output_path()`, `main()` |

Il est importe par **4 autres modules** : `run_incremental_session_v2`, `run_phase_c_lot_v2`, `heatmap_export`, et 3 fichiers de tests. C'est le module le plus couple du package.

**Suggestion de scission** :

| Nouveau module | Contenu extrait |
|---------------|-----------------|
| `review_engine.py` | `review_candidates_v2()`, `select_review_ids()`, `sample_intervention_ids()`, `validate_fallback_invariants()` |
| `io_v2.py` | `write_outputs_v2()`, `read_outputs_v2()`, `summarize_outputs_v2()`, `summarize_output_file()`, `write_comparison_summary()` |
| `run_pilot_v2.py` | Reduit a `build_provider()`, `main()`, et les imports |

`load_interventions_for_source()` devrait migrer vers un futur `xml_parser.py` (cf. diagnostic 5).

---

## Diagnostic 3 — Duplication de fonctions utilitaires

4 fonctions identiques copiees dans plusieurs modules :

| Fonction | Modules (def) | Suggestion |
|----------|--------------|------------|
| `_as_int()` | `context_builder`, `run_pilot_v2`, `heatmap_export` | → `paths.py` ou `utils.py` |
| `_display_path()` | `run_pilot_v2`, `run_phase_c_lot_v2`, `run_incremental_session_v2` + `build_phase_c_lot` | → `paths.py` |
| `_session_slug()` | `run_pilot_v2`, `run_phase_c_lot_v2`, `run_incremental_session_v2` | → `paths.py` |
| `_normalize_syceron_date()` | `source_acquisition`, `source_inventory` | → `paths.py` |

**Suggestion** : creer `src/assemblee_contextualization/paths.py` avec ces 4 fonctions + `ROOT_DIR`, `SOURCE_DIR`, `INTERIM_DIR`. Chaque module importe depuis ce point unique.

---

## Diagnostic 4 — `source_inventory.py` duplique `source_acquisition.py`

Les deux modules parsent les metadonnees XML des seances :

| aspect | `source_acquisition.py` | `source_inventory.py` |
|--------|------------------------|----------------------|
| Parsing XML metadonnees | `read_session_xml_metadata()` — complet, avec `iterparse`, verifie root tag, contenu, date, label | `parse_local_session_xml()` — simplifie, stop apres 3 champs trouves |
| Normalisation date | `_normalize_syceron_date()` | `_normalize_syceron_date()` (copie identique) |
| Dataclass resultat | `SessionXmlMetadata` | `LocalSessionXml` (memes 5 champs) |

**Verdict** : `LocalSessionXml` et `SessionXmlMetadata` ont les **memes 5 champs exactement** (`source_file`, `seance_id`, `seance_date`, `seance_date_label`, `local_path`). Le parsing est duplique avec des niveaux de validation differents.

**Suggestion** :
- Unifier sur `SessionXmlMetadata` + `read_session_xml_metadata()` comme seule source de parsing
- `source_inventory.py` appelle `read_session_xml_metadata()` au lieu de `parse_local_session_xml()`
- Supprimer `LocalSessionXml`, `_normalize_syceron_date()` de `source_inventory`

---

## Diagnostic 5 — Couplage ascendant vers `build_assemblee_pilot.py`

3 modules du package importent depuis le script parent :

| Module | Imports depuis `build_assemblee_pilot` |
|--------|---------------------------------------|
| `run_pilot_v2.py` | `NS`, `SOURCE_DIR`, `child_text`, `iter_paragraphs` |
| `source_inventory.py` | `ROOT_DIR`, `SOURCE_DIR` |
| `source_manifest.py` | `ROOT_DIR`, `SOURCE_DIR` |

C'est un couplage **inverse** : le sous-package depend d'un script CLI parent. Ce script melange parsing XML, regles lexicales, exports CSV/JSON, et constantes de chemins.

**Suggestion** (dans l'ordre) :
1. `ROOT_DIR`, `SOURCE_DIR`, `INTERIM_DIR` → `paths.py` (diagnostic 3)
2. `NS`, `child_text`, `element_text`, `iter_paragraphs`, `InterventionRow` → nouveau `xml_parser.py` dans le package
3. `build_assemblee_pilot.py` reduit a CLI + orchestration, importe depuis le package

---

## Diagnostic 6 — `contracts.py` melange V1 et V2

Le fichier contient **simultanement** :
- Enum V1 `Decision` (3 valeurs)
- Dataclass V1 `ContextualReviewOutput` + `validate_review_output()`
- Enum V2 `ScopeLevel`, `SignalCategory`
- Dataclass V2 `ContextualReviewOutputV2` + `validate_review_output_v2()`
- Dataclasses partagees : `SourceRef`, `ContextPayload`, `LocalContext`, etc.

Les types V1 ne sont consommes que par les 4 modules V1 morts + leurs tests.

**Suggestion** : pas de scission pour l'instant — le fichier fait 306 lignes, ce qui reste gerable. Mais quand le code V1 sera isole dans `legacy/`, les types V1 (`Decision`, `ContextualReviewOutput`, `validate_review_output`) pourront migrer avec.

---

## Diagnostic 7 — Modules sains, aucune action requise

| Module | Note |
|--------|------|
| `providers.py` (11 LOC) | Interface ABC propre, bien consommee |
| `context_builder.py` (102 LOC) | Responsabilite unique, bien testee |
| `processing_journal.py` (71 LOC) | Complet, validation stricte, bien isole |
| `source_acquisition.py` (287 LOC) | Fonctionnel, hash SHA-256, gestion ZIP correcte |
| `mock_provider_v2.py` (35 LOC) | Minimal, correct |
| `mistral_provider_v2.py` (188 LOC) | Prompt long mais coherent. Externalisation souhaitable mais non urgente |
| `env.py` (30 LOC) | Artisanal mais fonctionnel pour les besoins actuels |

---

## Synthese des propositions

| # | Action | Fichiers touches | Impact | Effort |
|---|--------|-----------------|--------|--------|
| **A** | Isoler V1 dans `legacy/` | `reviewer.py`, `mock_provider.py`, `mistral_provider.py`, `run_pilot.py` + tests | Nettoie le package visible | Faible |
| **B** | Creer `paths.py` — centraliser `ROOT_DIR`, `_display_path`, `_session_slug`, `_as_int`, `_normalize_syceron_date` | 7 modules importeurs | Elimine 4 doublons | Faible |
| **C** | Scinder `run_pilot_v2.py` en `review_engine.py` + `io_v2.py` | `run_pilot_v2` + 4 importeurs | Reduit le God module | Moyen |
| **D** | Unifier `LocalSessionXml` / `SessionXmlMetadata` et le parsing XML metadonnees | `source_inventory` + `source_acquisition` | Elimine 1 dataclass + 2 fonctions dupliquees | Faible |
| **E** | Extraire `xml_parser.py` (NS, iter_paragraphs, child_text) depuis `build_assemblee_pilot.py` | `run_pilot_v2`, `build_assemblee_pilot` | Inverse le couplage ascendant | Moyen |

**Ordre recommande** : B → A → D → C → E (chaque etape est testable isolement).
