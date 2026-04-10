# OBSERVATOIRE

Structure minimale de travail pour la collecte et l'analyse de débats de l'Assemblee nationale a partir d'un corpus XML Syceron.

## Arborescence

- `data/raw/assemblee/zips/` : archives originales conservees telles quelles
- `data/raw/assemblee/extracted/` : extractions XML conservees telles quelles
- `data/interim/` : fichiers intermediaires issus de futures transformations
- `data/exports/` : sorties preparees pour visualisation ou diffusion
- `src/` : futur code de collecte, parsing et export
- `tests/` : futurs tests du pipeline
- `notebooks/` : exploration ponctuelle
- `logs/` : journaux d'execution

## Etat actuel

- Le ZIP original a ete conserve dans `data/raw/assemblee/zips/`.
- L'extraction initiale a ete deplacee dans `data/raw/assemblee/extracted/syceron_initial_import/`.
- La hierarchie interne `xml/compteRendu/` a ete conservee.
