# Audit complet du projet OBSERVATOIRE

Date : 18 avril 2026

---

## 1. Vue d'ensemble

**Objet** : pipeline d'analyse de debats parlementaires de l'Assemblee nationale
(corpus XML Syceron), avec detection de signaux lies a la haine, au racisme, a la
xenophobie, a la discrimination, et contextualisation via LLM (Mistral).

**Etat d'avancement** : Phases A a F cloturees ; Phase G (consolidation) a ouvrir.
Quinze seances traitees (N191 a N205) avec export heatmap pour chacune.

### Metriques cles

| Indicateur                  | Valeur       |
|-----------------------------|-------------|
| Lignes source (`src/`)      | 3 214 LOC   |
| Lignes tests (`tests/`)     | 3 007 LOC   |
| Ratio test/src              | 0,94        |
| Modules source              | 21 fichiers |
| Modules test                | 20 fichiers |
| Artefacts interim           | ~70 fichiers|
| Exports D3 versiones        | 34 fichiers |
| Commits (branche `main`)    | ~50+        |

---

## 2. Architecture actuelle

### 2.1 Structure du code

```
src/
├── build_assemblee_pilot.py         ← parsing XML, regles lexicales, CSV/JSON
├── build_assemblee_phase_c_lot.py   ← lot multi-seances
└── assemblee_contextualization/
    ├── contracts.py                 ← contrats V1 + V2, enums, validation
    ├── providers.py                 ← interface abstraite (ABC)
    ├── mock_provider.py             ← provider V1 mock
    ├── mock_provider_v2.py          ← provider V2 mock
    ├── mistral_provider.py          ← provider V1 Mistral
    ├── mistral_provider_v2.py       ← provider V2 Mistral
    ├── context_builder.py           ← construction payload contextuel
    ├── reviewer.py                  ← orchestrateur V1
    ├── run_pilot.py                 ← CLI pilote V1
    ├── run_pilot_v2.py              ← CLI pilote V2 + fonctions partagees
    ├── run_phase_c_lot_v2.py        ← lot V2
    ├── run_incremental_session_v2.py← traitement incremental avec journal
    ├── processing_journal.py        ← journal JSONL anti-doublons
    ├── source_acquisition.py        ← import ZIP/XML, hash, validation
    ├── source_inventory.py          ← inventaire local des seances
    ├── source_manifest.py           ← manifest enrichi a partir du ZIP
    ├── heatmap_export.py            ← export heatmap pour D3
    └── env.py                       ← chargement .env maison
```

### 2.2 Flux de donnees

```
[ZIP Syceron] ──► [source_acquisition] ──► data/raw/.../compteRendu/*.xml
                                                    │
                         [build_assemblee_pilot] ◄──┘
                              │
                       parsing XML + regles lexicales
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
            CSV interventions     JSON D3 timeline
                    │
         [context_builder] ──► payload contextuel
                    │
         [provider V2] ──► sortie qualifiee
                    │
         [run_incremental] ──► JSONL reviews + journal
                    │
         [heatmap_export] ──► JSON/HTML heatmap D3
```

---

## 3. Points forts

### 3.1 Rigueur methodologique
- Contrat V2 tres bien defini avec combinaisons autorisees strictes, validees
  par code (`validate_v2_combination`, `validate_review_output_v2`).
- Separation nette entre fallback technique et hors-perimetre substantiel.
- Politique editoriale explicite : "signal a revoir, sans jugement automatique".

### 3.2 Architecture provider
- Pattern Strategy correct : `ContextualReviewProvider` (ABC) avec
  `MockContextualReviewProvider[V2]` et `MistralContextualReviewProvider[V2]`.
- Les providers de test permettent le developpement offline.

### 3.3 Couverture de tests
- Ratio test/code excellent (0,94).
- Tests sur les contrats, les combinaisons V2, les providers, le journal,
  l'acquisition de source, le manifest, la heatmap.

### 3.4 Anti-regression journal
- Journal JSONL avec anti-doublons fonctionnel pour le traitement incremental.

### 3.5 Tracabilite
- Chaque sortie porte `model_provider`, `model_name`, `is_fallback`, `limits`.
- Le manifest trace hash, date, statut de chaque seance.

---

## 4. Problemes identifies — par priorite

### P1 — CRITIQUE

#### 4.1 Absence de gestion de projet Python (`pyproject.toml`)

- **Aucun fichier** `pyproject.toml`, `setup.py`, `setup.cfg` ni
  `requirements.txt`.
- Les dependances (`mistralai`, etc.) ne sont pas declarees.
- Impossible de reproduire l'environnement de facon fiable.
- `pytest` n'est pas installe dans le venv.

**Recommandation** : creer un `pyproject.toml` minimal avec sections
`[project]`, `[project.optional-dependencies]` (dev = pytest, ruff, mypy).

#### 4.2 Absence de linter/formatter/type-checker dans le workflow

- Ni `ruff`, ni `black`, ni `mypy`, ni `flake8` ne sont installes.
- Pas de configuration CI.
- Risque : deviations de style, bugs de type silencieux.

**Recommandation** : ajouter `ruff` pour lint+format, `mypy --strict` pour
le typage, dans `pyproject.toml` + pre-commit.

---

### P2 — IMPORTANT

#### 4.3 Duplication de constantes et fonctions utilitaires

Quatre fonctions identiques copiees dans plusieurs modules :

| Fonction                    | Occurrences (def) |
|-----------------------------|-------------------|
| `_normalize_syceron_date()` | 2 (source_acquisition, source_inventory) |
| `_display_path()`           | 4 (build_phase_c, run_pilot_v2, run_phase_c, run_incremental) |
| `_session_slug()`           | 3 (run_pilot_v2, run_phase_c, run_incremental) |
| `_as_int()`                 | 3 (context_builder, run_pilot_v2, heatmap_export) |

Quatre definitions distinctes de `ROOT_DIR` :
- `build_assemblee_pilot.py` : `Path(__file__).resolve().parents[1]`
- `env.py` : `Path(__file__).resolve().parents[2]`
- `processing_journal.py` : `Path(__file__).resolve().parents[2]`
- `run_pilot.py` / `run_pilot_v2.py` : `Path(__file__).resolve().parents[2]`

**Risque** : divergence silencieuse si l'une des copies est modifiee.

**Recommandation** : extraire un module `src/assemblee_contextualization/paths.py`
(ou `utils.py`) centralisant `ROOT_DIR`, `SOURCE_DIR`, `INTERIM_DIR`,
`_display_path`, `_session_slug`, `_normalize_syceron_date`, `_as_int`.

#### 4.4 Couplage fort `build_assemblee_pilot` ↔ sous-package contextualization

Plusieurs modules du sous-package importent directement depuis le script
racine `build_assemblee_pilot.py` :
- `source_inventory.py` → `ROOT_DIR, SOURCE_DIR`
- `source_manifest.py` → `ROOT_DIR, SOURCE_DIR`
- `run_pilot_v2.py` → `NS, SOURCE_DIR, child_text, iter_paragraphs`
- `run_phase_c_lot_v2.py` → `PHASE_C_LOT_FILES, OUTPUT_PATH`
- `build_assemblee_phase_c_lot.py` → `INTERIM_DIR, ROOT_DIR, InterventionRow,
  parse_source_file, write_csv`

Ce script cumule :
1. parsing XML generique,
2. regles lexicales,
3. export CSV/JSON,
4. constantes globales de chemins,
5. point d'entree CLI.

C'est le fichier le plus long (358 lignes) et le plus couple du projet.

**Recommandation** : scinder `build_assemblee_pilot.py` en :
- `src/assemblee_contextualization/xml_parser.py` : parsing XML pur
  (`iter_paragraphs`, `element_text`, `child_text`, `NS`, `InterventionRow`)
- `src/assemblee_contextualization/signal_rules.py` : `SIGNAL_RULES`,
  `signal_hit_from_text`, `normalize_for_signal`
- `src/assemblee_contextualization/paths.py` : chemins et constantes
- `src/build_assemblee_pilot.py` : reduit a la CLI `main()`

#### 4.5 Coexistence V1/V2 non isolee

Deux systemes coexistent :
- V1 : `Decision` (validated_signal/false_positive/ambiguous), `reviewer.py`,
  `mock_provider.py`, `mistral_provider.py`, `run_pilot.py`
- V2 : `ScopeLevel` + `SignalCategory`, `*_v2.py`

Les contrats V1 et V2 vivent dans le meme `contracts.py`.
Le code V1 n'est plus utilise en production (Phase B close, V2 est le
contrat cible) mais n'est pas marque comme deprecie.

**Recommandation** :
- Ajouter un commentaire `# DEPRECATED — V1, conserve pour historique` en
  tete des classes/fonctions V1.
- A terme, deplacer V1 dans un sous-module `legacy/` ou le supprimer.

---

### P3 — AMELIORATION

#### 4.6 `env.py` : chargement `.env` artisanal

Le module `env.py` reimplemente `dotenv`. Ce code ad hoc ne gere pas les
variables multi-lignes, les commentaires en fin de ligne, ni l'export.

**Recommandation** : utiliser `python-dotenv` (deja standard) ou documenter
les limites de l'implementation maison.

#### 4.7 Chemins en dur et constantes module-level

Les paths par defaut (`DEFAULT_REVIEW_PATH`, `OUTPUT_PATH`, `CSV_PATH`, etc.)
sont calcules au chargement du module. Cela :
- rend les tests dependants du filesystem reel s'ils ne patchent pas,
- empeche la configuration par environnement.

**Recommandation** : passer les chemins au constructeur ou en argument ;
retarder le calcul des valeurs par defaut dans les fonctions.

#### 4.8 Prompt LLM en dur dans le code Python

`SYSTEM_PROMPT_V2` et `USER_PROMPT_TEMPLATE_V2` (80+ lignes) sont
integralement codes dans `mistral_provider_v2.py`. Modifier le prompt exige
de modifier du code Python.

**Recommandation** : externaliser les prompts dans des fichiers texte ou
YAML dans un dossier `prompts/`, charges au runtime.

#### 4.9 Pas de retry / rate-limit pour l'API Mistral

Les providers Mistral appellent `client.chat.complete(...)` une seule fois.
En cas de timeout ou rate-limit 429, le fallback silencieux est produit.

**Recommandation** : ajouter un retry avec backoff exponentiel (
`tenacity` ou boucle simple) avec un maximum de 2-3 tentatives.

#### 4.10 `.gitignore` heatmap en croissance lineaire

Chaque nouvelle seance exige 2 lignes `!data/exports/d3/..._nXXX.*` dans
`.gitignore`. C'est une dette d'exploitation croissante.

**Recommandation** : restructurer les exports en sous-dossiers par type
(ex: `data/exports/d3/heatmaps/`) ignores par pattern glob, plutot qu'en
liste d'exceptions nominatives. Ou utiliser un pattern `!data/exports/d3/assemblee_session_heatmap_*.{html,json}`.

#### 4.11 Absence de logging

Le projet utilise `print()` exclusivement. Aucun `import logging`.

**Recommandation** : passer a `logging` standard avec niveaux INFO/WARNING/ERROR.
Cela permettra filtrages, rotation, et integration future.

---

### P4 — SUGGESTIONS

#### 4.12 Pas de `__main__.py` pour le package

`assemblee_contextualization` n'a pas de `__main__.py`; les points d'entree
CLI sont disperses dans `run_pilot.py`, `run_pilot_v2.py`,
`run_incremental_session_v2.py`, etc.

**Recommandation** : un `__main__.py` avec sous-commandes (via `argparse`
sous-parseurs) ou un outil CLI leger comme `click`.

#### 4.13 Tests non executables dans l'etat actuel

`pytest` n'est pas installe dans le venv. Les tests ne peuvent pas etre
lances sans intervention manuelle. Pas de CI configuree.

**Recommandation** : script `Makefile` ou `justfile` avec cibles :
`make install`, `make test`, `make lint`.

#### 4.14 Documentation utilisateur limitee

Le README est minimal (12 lignes utiles). Il n'y a pas :
- d'instructions d'installation,
- de guide de demarrage rapide,
- d'exemples d'utilisation des CLI.

Les docs internes (roadmap, contrats) sont riches mais orientees projet,
pas utilisateur.

#### 4.15 Aucun mecanisme de configuration

Pas de fichier de configuration centralisee (ni YAML, ni TOML, ni classe
`Settings`). Tous les parametres (window, sample_size, start_date, etc.)
sont soit en dur, soit en argument CLI.

---

## 5. Graphe de dependances inter-modules

```
build_assemblee_pilot  ◄──────┐
        │                      │
        ▼                      │
build_assemblee_phase_c_lot    │
                               │
assemblee_contextualization/   │
├── contracts ◄── providers    │
├── env                        │
├── context_builder ──► contracts
├── reviewer ──► context_builder, contracts, providers
├── mock_provider[_v2] ──► providers, contracts
├── mistral_provider[_v2] ──► providers, contracts, env
├── run_pilot ──► context_builder, env, mistral_provider, mock_provider, reviewer
├── run_pilot_v2 ──────────► build_assemblee_pilot (NS, SOURCE_DIR, etc.)
├── run_phase_c_lot_v2 ───► run_pilot_v2, build_assemblee_phase_c_lot
├── run_incremental ───────► run_pilot_v2, processing_journal, source_manifest
├── processing_journal
├── source_acquisition
├── source_inventory ──────► build_assemblee_pilot (ROOT_DIR, SOURCE_DIR)
├── source_manifest ───────► source_acquisition, source_inventory,
│                             processing_journal, build_assemblee_pilot
└── heatmap_export ────────► run_pilot_v2, processing_journal, contracts
```

Point de fragilite : `build_assemblee_pilot` est importe par 5 modules du
sous-package. C'est un couplage ascendant (un sous-package qui depend d'un
script parent) qui devrait etre inverse.

---

## 6. Matrice de priorites

| # | Priorite  | Action                                        | Effort | Impact |
|---|-----------|-----------------------------------------------|--------|--------|
| 1 | CRITIQUE  | Creer `pyproject.toml` + `requirements`       | Faible | Fort   |
| 2 | CRITIQUE  | Installer et configurer ruff + mypy            | Faible | Fort   |
| 3 | IMPORTANT | Extraire `paths.py` (ROOT_DIR, utils)         | Moyen  | Fort   |
| 4 | IMPORTANT | Scinder `build_assemblee_pilot.py`             | Moyen  | Fort   |
| 5 | IMPORTANT | Marquer V1 deprecie, isoler                    | Faible | Moyen  |
| 6 | AMELIOR.  | Externaliser prompts LLM                       | Faible | Moyen  |
| 7 | AMELIOR.  | Ajouter retry provider Mistral                 | Faible | Moyen  |
| 8 | AMELIOR.  | Remplacer `env.py` par `python-dotenv`         | Faible | Faible |
| 9 | AMELIOR.  | Passer a `logging` standard                    | Moyen  | Moyen  |
| 10| AMELIOR.  | Simplifier `.gitignore` exports                | Faible | Faible |
| 11| SUGGEST.  | README enrichi + instructions install          | Faible | Moyen  |
| 12| SUGGEST.  | Ajouter Makefile/justfile                      | Faible | Moyen  |
| 13| SUGGEST.  | CLI unifiee `__main__.py`                      | Moyen  | Faible |

---

## 7. Recommandation d'approche

**Phase immediate (avant nouvelle extension)** :
1. Creer `pyproject.toml` avec dependances et config outils.
2. Executer ruff + mypy, corriger les erreurs.
3. Lancer les tests, confirmer le vert.

**Phase suivante (pendant Phase G)** :
4. Extraire `paths.py`, eliminer les duplications.
5. Scinder `build_assemblee_pilot.py`.
6. Marquer V1 deprecie.

**A planifier (Phase H ou apres)** :
7. Externalisation prompts, retry Mistral, logging, CI.

---

*Fin du rapport d'audit.*
