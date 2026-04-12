# Roadmap Assemblee

## Statut du document

Ce document est la source de verite active pour le planning Assemblee a partir
du pivot V2.

Les anciens fichiers restent utiles comme historique, mais ne pilotent plus les
prochaines etapes :

- `docs/assemblee_signaux_tasks.md` : historique de la phase signaux et du
  pipeline pilote.
- `docs/assemblee_contextualization_tasks.md` : historique de la
  contextualisation v0/v1.
- `docs/assemblee_contextualization_contract_v2.md` : reference du contrat V2.
- `docs/assemblee_roadmap.md` : planning actif pour la suite.

Les fichiers `docs/plan.md`, `docs/assemblee_signaux_plan.md` et
`docs/assemblee_contextualization_plan.md` restent des documents de cadrage
historique. Ils ne remplacent pas cette roadmap.

## Perimetre

Le projet OBSERVATOIRE reste centre sur :

- haine ;
- racisme ;
- xenophobie ;
- discrimination ;
- ciblage problematique de groupes relevant du perimetre discriminatoire,
  notamment origine, nationalite, ethnicite reelle ou supposee, religion, ou
  categories comparables du meme perimetre.

Le projet ne doit pas devenir un observatoire general de la tension politique,
du conflit parlementaire, de la critique institutionnelle ou du climat civique.

## Etat actuel

Fait :

- pipeline Assemblee pilote sur N191 ;
- parsing local du XML pilote ;
- export tabulaire des interventions ;
- export JSON et timeline D3 pilote ;
- detection rule-based de signaux candidats ;
- tableau de revue humaine pilote ;
- contextualisation V1 avec provider mock et Mistral ;
- tests de la couche contextualisation V1 ;
- test A/B N191 / N190 pour observer la robustesse methodologique ;
- contrat V2 documente et teste avec `scope_level`, `signal_category`,
  `is_fallback`, `needs_human_review`.

En cours :

- Phase B - Stabilisation methode V2.

A faire :

- Phase C - Extension petit lot Assemblee ;
- Phase D - Corpus local complet ;
- Phase E - Visualisation ;
- Phase F - Automatisation collecte.

Explicitement remis a plus tard :

- Phase G - Application ;
- scoring definitif ;
- modele de classification entraine ;
- interpretation politique automatisee ;
- extension hors corpus Assemblee.

## Decisions actees

- V1 reste intact pour historique et pilote.
- V2 devient le contrat cible.
- Mistral ne produit pas de verdict moral.
- Les regles lexicales deviennent secondaires : elles peuvent aider a reperer
  des candidats, mais ne doivent plus etre un filtre bloquant unique.
- `is_fallback = true` ne doit jamais etre compte comme un vrai hors-perimetre
  substantiel.
- D3 reste une visualisation prudente : elle ne doit pas presenter les sorties
  comme des verdicts.

## Phase B - Stabilisation methode V2

Statut : en cours.

Objectif : terminer la methode avant extension.

Taches minimales :

- garder le contrat V2 comme contrat cible ;
- produire un run V2 minimal separe sur le pilote N191 ;
- tester le V2 sur N190 en comparaison ;
- decider le role exact des regles lexicales comme aide secondaire ;
- documenter les limites methodologiques ;
- produire une note de stabilisation.

Critere de sortie :

- un flux V2 minimal tourne ;
- les sorties V2 sont validees par le contrat ;
- N191 et N190 ont ete comparees ;
- les regles lexicales ne sont plus un filtre bloquant unique ;
- une note de stabilisation existe.

## Phase C - Extension petit lot Assemblee

Statut : a faire.

Objectif : tester sur quelques seances locales avant tout le corpus.

Taches :

- selectionner un petit lot de seances ;
- parser le lot ;
- produire les sorties structurees ;
- appliquer le flux V2 ;
- controler les faux positifs, faux negatifs et cas ambigus ;
- verifier les couts et les volumes.

Critere de sortie :

- methode validee sur plusieurs seances ;
- limites et erreurs documentees.

## Phase D - Corpus local complet

Statut : a faire.

Objectif : appliquer la methode stabilisee au corpus local Assemblee.

Taches :

- parser le corpus local ;
- produire les exports multi-seances ;
- generer des agregations par seance, date, `scope_level`,
  `signal_category` ;
- exclure `is_fallback = true` des metriques substantielles.

Critere de sortie :

- exports multi-seances produits ;
- agregations V2 disponibles ;
- fallbacks exclus des metriques substantielles.

## Phase E - Visualisation

Statut : a faire.

Objectif : reinjecter prudemment les resultats V2 dans la visualisation.

Taches :

- choisir les champs V2 a afficher ;
- adapter le JSON D3 ;
- adapter la timeline ;
- verifier que la visualisation ne produit pas de verdict.

Critere de sortie :

- timeline adaptee aux champs V2 retenus ;
- rendu lisible ;
- absence de formulation ou codage visuel assimilable a un verdict.

## Phase F - Automatisation collecte

Statut : a faire.

Objectif : automatiser la recuperation et l'actualisation des XML.

Taches :

- identifier la source de collecte ;
- automatiser le telechargement ;
- eviter les doublons ;
- mettre a jour le manifest ;
- preparer le parsing incremental.

Critere de sortie :

- collecte reproductible ;
- manifest mis a jour ;
- parsing incremental prepare.

## Phase G - Application

Statut : remis a plus tard.

Objectif : passer des scripts a une application utilisable.

Taches :

- definir l'interface minimale ;
- definir le mode d'acces aux donnees ;
- brancher les exports stabilises ;
- decider ce qui est interne et ce qui est publiable.

## Prochaines taches immediates

1. Creer un run V2 minimal separe sur N191.
2. Tester V2 sur N190.
3. Produire une note de stabilisation Phase B.

## Ne pas faire maintenant

- pas de D3 ;
- pas d'extension corpus complet ;
- pas d'automatisation collecte ;
- pas de nouvelle taxonomie ;
- pas de refonte architecture ;
- pas d'application UI tant que Phase B n'est pas close.

## Points de vigilance

- Ne pas elargir `core` a des tensions politiques ordinaires.
- Ne pas laisser `adjacent` devenir une categorie fourre-tout.
- Ne pas compter `is_fallback = true` comme un vrai hors-perimetre.
