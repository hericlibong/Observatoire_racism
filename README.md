# OBSERVATOIRE

Pipeline de collecte, parsing et contextualisation de debats parlementaires de
l'Assemblee nationale a partir d'un corpus XML Syceron.

Le perimetre du projet reste limite aux signaux lies a la haine, au racisme, a
la xenophobie, a la discrimination et au ciblage problematique de groupes du
perimetre discriminatoire. Le projet ne vise pas un observatoire general de la
tension politique ou du conflit parlementaire.

## Demarrage developpement

Prerequis :

- Python 3.12 ou plus recent ;
- un environnement virtuel local.

Installation editable avec les dependances de developpement :

```bash
python -m pip install -e '.[dev]'
```

Tests depuis la racine :

```bash
python -m pytest tests/ -v
```

Lint :

```bash
python -m ruff check src tests
```

Formatage :

```bash
python -m ruff format src tests
```

Type-check progressif :

```bash
python -m mypy src tests
```

Les providers Mistral lisent les secrets depuis `.env` via `MISTRAL_API_KEY`.
Les tests existants n'appellent pas l'API Mistral et doivent rester executables
hors reseau.

## Arborescence

- `data/raw/assemblee/zips/` : archives originales conservees telles quelles
- `data/raw/assemblee/extracted/` : extractions XML conservees telles quelles
- `data/interim/` : fichiers intermediaires issus de futures transformations
- `data/exports/` : sorties preparees pour visualisation ou diffusion
- `src/` : code de collecte, parsing, contextualisation et export
- `tests/` : tests pytest du pipeline
- `notebooks/` : exploration ponctuelle
- `logs/` : journaux d'execution

## Etat actuel

- Le ZIP original a ete conserve dans `data/raw/assemblee/zips/`.
- L'extraction initiale a ete deplacee dans
  `data/raw/assemblee/extracted/syceron_initial_import/`.
- La hierarchie interne `xml/compteRendu/` a ete conservee.
- Les exports N191 a N205 existants servent de references de non-regression
  pour la Phase G.
