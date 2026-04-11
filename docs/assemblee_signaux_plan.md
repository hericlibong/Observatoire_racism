# Plan Assemblee - signaux candidats

## Objectif immediat

Enrichir le fichier pilote Assemblee avec des signaux candidats relisibles, puis les afficher dans une timeline D3 enrichie.

Le but de cette sequence est de produire un premier cadrage robuste sur un seul fichier avant d'etendre au corpus local.

## Definition de signal candidat

Un signal candidat est un passage repere automatiquement comme meritant une relecture, sans conclure automatiquement qu'il est raciste, discriminatoire ou haineux.

Il sert a orienter le controle humain, pas a produire un jugement.

## Perimetre actuel

- Source Assemblee : XML Syceron locaux de l'Assemblee nationale.
- Fichier pilote : `CRSANR5L17S2026O1N191.xml`.
- Timeline D3 : visualisation intra-seance ordonnee par intervention.

## Phases de travail

### Phase A - enrichir le fichier pilote

Objectif :

- ajouter des champs de signaux candidats au fichier pilote deja extrait ;
- garder une sortie lisible et controlable.

Livrables :

- export tabulaire pilote enrichi ;
- JSON D3 enrichi ;
- timeline D3 affichant les signaux candidats sans jugement automatique.

### Phase B - stabiliser la methode

Objectif :

- verifier les champs utiles ;
- clarifier les regles de detection ;
- documenter les limites.

Livrables :

- liste des champs conserves ;
- liste des regles de detection retenues ;
- notes sur les faux positifs, faux negatifs et cas ambigus.

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

### Phase E - ajouter la couche contextuelle

Objectif :

- ajouter les informations utiles pour relire les signaux dans leur contexte ;
- ne pas transformer le signal candidat en score moral.

Livrables :

- contexte de seance et de point de debat ;
- liens ou references source si disponibles ;
- affichage D3 enrichi avec contexte de lecture.

## Remis a plus tard

- qualification automatique comme raciste, discriminatoire ou haineux ;
- scoring definitif ;
- tableau de bord consolide ;
- base de donnees ;
- analyse statistique globale ;
- extension hors corpus Assemblee ;
- modele de classification entraine ;
- interpretation politique automatisee.
