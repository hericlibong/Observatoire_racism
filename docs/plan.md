# Plan de travail

## Objectif immediat

Produire un premier jeu de donnees fiable a partir d'un seul fichier XML de compte rendu, puis alimenter une premiere visualisation D3 en timeline intra-seance. La granularite de base est : 1 ligne = 1 paragraphe / intervention.

## Source actuelle exploitee

- Source de depart : XML Syceron de l'Assemblee nationale deja ranges dans `data/raw/assemblee/extracted/`
- Fichier pilote fige pour le premier jalon : `CRSANR5L17S2026O1N191.xml`
- Chemin de reference : `data/raw/assemblee/extracted/syceron_initial_import/syseron.xml/xml/compteRendu/CRSANR5L17S2026O1N191.xml`

## Regle de cadrage

- Le fichier pilote ne change pas pendant le premier jalon technique.
- Le parsing effectif du jalon 1 ne vise que ce fichier.
- L'inventaire source prepare l'extension future du corpus, sans remplacer le parsing du fichier pilote.

## Ordre des prochaines etapes

1. Figer `CRSANR5L17S2026O1N191.xml` comme fixture de reference.
2. Reperer dans ce XML les champs vraiment fiables et repetables.
3. Definir le schema minimal `interventions` en ne gardant que les champs fiables issus du XML.
4. Definir la structure de `data/interim/assemblee/source_manifest.json` pour inventorier les fichiers sources.
5. Extraire les interventions du fichier pilote au niveau paragraphe avec un ordre de lecture strict dans la seance.
6. Produire un export tabulaire simple pour controle humain.
7. Produire un export JSON leger pour D3.
8. Preparer une premiere timeline intra-seance en D3.
9. Evaluer les manques de schema avant d'etendre a plusieurs XML.

## Jeux de donnees a produire d'abord

### 1. Table `interventions`

Champs minimaux recommandes :

- `intervention_id`
- `seance_id`
- `ordre`
- `point_titre`
- `orateur_nom`
- `orateur_qualite`
- `code_grammaire`
- `roledebat`
- `texte`
- `nb_mots`
- `nb_caracteres`

Remarques :

- Ne pas supposer `groupe_politique` garanti au depart.
- Conserver d'abord uniquement les champs fiables issus du XML.

### 2. Export de visualisation

Un JSON derive de `interventions`, limite aux champs utiles a la timeline D3 du premier XML test.

### 3. Inventaire source

Un fichier `data/interim/assemblee/source_manifest.json` dedie a l'inventaire du corpus source.

Champs minimaux attendus par entree :

- `nom_fichier`
- `chemin`
- `taille_octets`
- `mtime_local`

Usage :

- lister les fichiers presents localement
- preparer un futur mecanisme d'inventaire
- ne pas remplacer le parsing
- ne pas redefinir le fichier pilote

## Premiere visualisation D3 visee

Une timeline intra-seance, ordonnee par `ordre`, avec une marque visuelle par intervention. La couleur represente une intensite de signal candidat, jamais un jugement moral. Cette premiere vue sert a verifier la structure du debat a l'echelle d'une seule seance, pas a produire encore des agregations journalieres.

## Remis a plus tard

- courbes et bar charts journaliers
- traitement multi-fichiers complet
- enrichissement par groupe politique
- base de donnees
- frontend complet
- tableaux de bord consolides
- indicateurs interpretes ou scores stabilises
