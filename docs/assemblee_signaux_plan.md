# Plan Assemblee - signaux candidats

## Objectif immediat

Piloter la detection, la stabilisation et la visualisation des signaux candidats Assemblee.

Le fichier pilote reste le point d'appui. La contextualisation existe dans une brique separee et n'est pas documentee ici.

## Definition de signal candidat

Un signal candidat est un passage repere automatiquement comme meritant une relecture, sans conclure automatiquement qu'il est raciste, discriminatoire ou haineux.

Il sert a orienter le controle humain, pas a produire un jugement.

## Perimetre actuel

- Source Assemblee : XML Syceron locaux de l'Assemblee nationale.
- Fichier pilote : `CRSANR5L17S2026O1N191.xml`.
- Export enrichi : `data/interim/assemblee/interventions_test.csv`.
- JSON D3 : `data/exports/d3/assemblee_pilot_timeline.json`.
- Timeline D3 : `data/exports/d3/assemblee_pilot_timeline.html`.
- Tableau de revue : `data/interim/assemblee/signals_review_pilot.csv`.

Hors perimetre de ce plan :

- contrats internes de contextualisation ;
- providers mock ou Mistral ;
- prompt provider ;
- orchestration agentique.

Ces points sont suivis dans les documents `assemblee_contextualization_*`.

## Phases de travail

### Phase A - enrichir le fichier pilote

Objectif :

- ajouter des champs de signaux candidats au fichier pilote deja extrait ;
- garder une sortie lisible et controlable ;
- alimenter la timeline D3 pilote.

Livrables :

- export tabulaire pilote enrichi ;
- JSON D3 enrichi ;
- timeline D3 affichant les signaux candidats sans jugement automatique ;
- tableau de revue humaine des signaux du fichier pilote.

### Phase B - stabiliser la methode

Objectif :

- consolider les regles rule-based ;
- verifier les faux positifs, faux negatifs et cas ambigus ;
- documenter les limites de la detection.

Livrables :

- liste des champs conserves ;
- liste des regles de detection retenues ;
- format minimal de sortie stabilise ;
- notes sur les faux positifs, faux negatifs et cas ambigus ;
- limites de methode documentees.

### Phase C - etendre au corpus local Assemblee

Objectif :

- appliquer la methode stabilisee aux XML Assemblee disponibles localement ;
- garder une trace des fichiers traites.

Livrables :

- manifest source mis a jour ;
- exports multi-fichiers simples ;
- controle sur un echantillon de fichiers.

### Phase D - automatiser la collecte

Objectif :

- preparer une collecte reproductible des nouvelles sources Assemblee ;
- separer collecte, extraction et visualisation.

Livrables :

- script ou commande de collecte ;
- regle de nommage et de rangement ;
- journal minimal des fichiers recuperes.

### Phase E - articuler signaux et contextualisation

Objectif :

- exploiter les sorties contextualisees sans dupliquer la brique de contextualisation ;
- comparer les signaux rule-based aux decisions contextualisees ;
- preparer une reinjection utile dans D3 ;
- eviter tout rendu interpretable comme un verdict.

Livrables :

- synthese des cas representatifs ;
- liste des faux positifs et cas ambigus utiles a la stabilisation ;
- choix des champs contextualises a ajouter au JSON D3 ;
- timeline D3 enrichie avec les champs retenus ;
- verification de lisibilite et de prudence du rendu.

## Remis a plus tard

- qualification automatique comme raciste, discriminatoire ou haineux ;
- scoring definitif ;
- tableau de bord consolide ;
- base de donnees ;
- analyse statistique globale ;
- extension hors corpus Assemblee ;
- modele de classification entraine ;
- interpretation politique automatisee.
