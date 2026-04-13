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

- Phase D - Corpus local complet.

A faire :

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

Statut : cloturee.

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

## Todo actif - Phase B

### Bloc 1 - Execution minimale V2 sur le pilote

- [x] Creer un run V2 minimal separe sur `CRSANR5L17S2026O1N191.xml`.
- [x] Creer ou adapter un provider V2 minimal sans casser V1.
- [x] Valider chaque sortie avec `validate_review_output_v2`.
- [x] Produire un export V2 dedie dans `data/interim/assemblee/`.
- [x] Verifier explicitement que `is_fallback = true` est present seulement
  dans le cas technique autorise.

### Bloc 2 - Controle methodologique sur une deuxieme seance

- [x] Executer le meme flux V2 sur `CRSANR5L17S2026O1N190.xml`.
- [x] Comparer N191 et N190 avec le meme schema V2.
- [x] Verifier que les sorties V2 ne restent pas dependantes du seul cas
  Nouvelle-Caledonie.

### Bloc 3 - Role exact des regles lexicales

- [x] Decrire noir sur blanc le role secondaire exact des regles lexicales :
  selection, cout, audit, comparaison, jamais decision finale seule.
- [x] Decider quelles regles actuelles sont conservees, resserrees ou
  retirees.

### Bloc 4 - Agregation prudente

- [x] Produire un mini resume agrege V2 sur N191 puis N190.
- [x] Exclure systematiquement `is_fallback = true` des metriques
  substantielles.
- [x] Verifier qu'un vrai `hors_perimetre / no_signal` reste distinct d'un
  fallback technique.

### Bloc 5 - Cloture Phase B

- [x] Rediger une note courte de stabilisation Phase B.
- [x] Lister ce qui est valide, ce qui reste fragile, et ce qui est reporte a la
  phase suivante.
- [x] Declarer explicitement le critere de sortie de Phase B atteint ou non.

## Decision Bloc 3 - Role des regles lexicales

Audit court : les regles lexicales actuelles sont definies dans
`src/build_assemblee_pilot.py` avec trois familles : `tension_politique`,
`designation_groupe`, `devalorisation`. Sur le pilote N191, elles produisent
26 candidats : 8 `tension_politique`, 11 `designation_groupe`, 7
`devalorisation`. Le run V2 Mistral N191 qualifie 24 de ces candidats en
`hors_perimetre / no_signal` et seulement 2 en `adjacent /
problematic_group_targeting`, tous deux issus de `designation_groupe`. Le run
V2 Mistral N190 relit 15 paragraphes et les qualifie tous en
`hors_perimetre / no_signal`. Aucun fallback technique n'est present dans ces
exports.

Role futur retenu : les regles lexicales restent une aide secondaire. Elles
peuvent servir a selectionner des candidats a relire, reduire le cout d'appel
modele, construire des echantillons d'audit et comparer les ecarts entre
signaux lexicaux et qualification V2. Elles ne produisent jamais la decision
finale, ne remplacent jamais `scope_level` / `signal_category`, et ne doivent
jamais redevenir un filtre bloquant unique : un flux V2 doit pouvoir relire des
paragraphes hors detection lexicale, notamment par echantillonnage neutre.

Decision par famille :

- `tension_politique` est retrogradee a un role exploratoire et d'audit. Les
  declencheurs comme `chaos`, `obstruction`, `passage en force` ou `violences`
  captent surtout la conflictualite parlementaire ordinaire ; ils ne doivent
  pas alimenter seuls une selection V2 substantielle.
- `devalorisation` est resserree. Les declencheurs generiques comme `honteuse`,
  `inacceptable`, `irresponsable`, `mepris` ou `une honte` ne suffisent pas :
  ils ne deviennent utiles que comme indices secondaires lorsqu'un groupe du
  perimetre discrimination / racisme / xenophobie est aussi present.
- `designation_groupe` est conservee mais fortement resserree. La famille est
  utile pour reperer des references collectives, mais elle est trop large en
  l'etat : les groupes politiques ou comportementaux comme
  `independantistes`, `anti-independantistes`, `loyalistes` ou `FLNKS` ne
  doivent pas etre traites comme des groupes du coeur de l'observatoire par
  defaut. Seules les designations avec ancrage clair dans l'origine,
  l'ethnicite reelle ou supposee, la nationalite, la religion ou une categorie
  comparable du perimetre peuvent justifier une priorisation V2 ; les autres
  restent des indices exploratoires.

Regle de methode : `adjacent` ne doit pas absorber les tensions politiques,
les critiques institutionnelles ou les conflits partisans detectes par lexique.
Il reste reserve aux cas frontieres avec ancrage plausible dans le perimetre de
l'observatoire.

## Decision Bloc 4 - Agregation prudente

Le mini resume agrege V2 de reference pour N191 et N190 est
`data/interim/assemblee/contextual_reviews_v2_n191_n190_summary.json`. Il
liste, par seance, le nombre de sorties relues, les distributions
`scope_level` et `signal_category`, le nombre de fallbacks techniques, le
nombre de vrais `hors_perimetre / no_signal`, et les distributions
substantielles hors fallback.

Regle retenue : toute sortie avec `is_fallback = true` est exclue des metriques
substantielles. Un vrai `hors_perimetre / no_signal / is_fallback = false`
reste compte comme hors-perimetre substantiel, distinct d'un fallback technique
`hors_perimetre / ambiguous / is_fallback = true`.

## Note de stabilisation Phase B

Decision : le critere de sortie de Phase B est atteint. La Phase B est
cloturee ; la methode V2 Assemblee est suffisamment stabilisee pour passer a
la Phase C. Cela ne signifie pas que l'application est terminee.

Valide :

- flux V2 minimal separe sur N191, avec sorties validees par le contrat V2 ;
- comparaison N191 / N190 avec le meme schema V2 ;
- role secondaire des regles lexicales confirme : selection, cout, audit et
  comparaison, jamais decision finale seule ni filtre bloquant unique ;
- agregation prudente consolidee : fallbacks techniques exclus des metriques
  substantielles, vrais `hors_perimetre / no_signal` conserves comme cas
  distincts.

Fragile :

- validation encore limitee a deux seances ;
- faible volume de cas substantiels pour eprouver les categories frontieres ;
- regles lexicales encore trop larges si elles sont utilisees sans controle
  V2.

Reporte a la Phase C :

- extension sur un petit lot local ;
- controle des faux positifs, faux negatifs et cas ambigus ;
- verification des couts et volumes avant corpus complet, D3, automatisation
  ou application.

## Phase C - Extension petit lot Assemblee

Statut : cloturee.

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

## Todo actif - Phase C

### Bloc 1 - Selection du petit lot local

- [x] Identifier les seances locales candidates pour le petit lot.
- [x] Retenir un petit lot suffisant pour tester la methode sans passer au
  corpus complet.
- [x] Noter la liste des seances retenues.

Note Bloc 1 - lot Phase C retenu :

- `CRSANR5L17S2026O1N191.xml` : reference Phase B, Nouvelle-Caledonie.
- `CRSANR5L17S2026O1N190.xml` : reference Phase B, lutte contre les fraudes
  sociales et fiscales.
- `CRSANR5L17S2026O1N120.xml` : questions au gouvernement, sujets varies dont
  gens du voyage.
- `CRSANR5L17S2025O1N150.xml` : session ordinaire 2024-2025, aide publique au
  developpement et prisons.
- `CRSANR5L17S2025E1N014.xml` : session extraordinaire 2025, statut de l'elu
  local.

Raison du choix : lot court de cinq seances, avec les deux references deja
testees et trois seances locales differenciees par periode, format ou theme.

Limites : selection faite au niveau fichier et sommaire, sans lecture complete,
sans parsing du lot et sans run V2. Le lot ne represente pas le corpus complet.

### Bloc 2 - Parsing et sorties structurees

- [x] Parser le petit lot retenu.
- [x] Produire les sorties structurees pour chaque seance du lot.
- [x] Verifier que les exports produits sont exploitables par le flux V2.

Note Bloc 2 - sortie structuree Phase C :

- sortie : `data/interim/assemblee/interventions_phase_c_lot.csv` ;
- seances representees : 5 ;
- interventions : 992 au total, dont `CRSANR5L17S2026O1N191` 159,
  `CRSANR5L17S2026O1N190` 240, `CRSANR5L17S2026O1N120` 102,
  `CRSANR5L17S2025O1N150` 280, `CRSANR5L17S2025E1N014` 211 ;
- verification V2 : CSV chargeable par le constructeur de contexte V2, sans
  provider et sans appel Mistral.

### Bloc 3 - Application du flux V2

- [x] Appliquer le flux V2 au petit lot.
- [x] Valider les sorties avec le contrat V2.
- [x] Conserver des exports V2 separes des sorties historiques.

Note Bloc 3 - exports V2 Phase C :

- providers utilises : `mock_v2` pour verifier la mecanique, puis
  `mistral_v2` pour les sorties reelles ;
- exports : `contextual_reviews_phase_c_lot_n191_v2_mock.jsonl`,
  `contextual_reviews_phase_c_lot_n190_v2_mock.jsonl`,
  `contextual_reviews_phase_c_lot_n120_v2_mock.jsonl`,
  `contextual_reviews_phase_c_lot_n150_v2_mock.jsonl`,
  `contextual_reviews_phase_c_lot_n014_v2_mock.jsonl` ;
- exports Mistral : `contextual_reviews_phase_c_lot_n191_v2_mistral.jsonl`,
  `contextual_reviews_phase_c_lot_n190_v2_mistral.jsonl`,
  `contextual_reviews_phase_c_lot_n120_v2_mistral.jsonl`,
  `contextual_reviews_phase_c_lot_n150_v2_mistral.jsonl`,
  `contextual_reviews_phase_c_lot_n014_v2_mistral.jsonl` ;
- resume : `data/interim/assemblee/contextual_reviews_phase_c_lot_v2_mock.json` ;
- resume Mistral :
  `data/interim/assemblee/contextual_reviews_phase_c_lot_v2_mistral.json` ;
- sorties V2 : N191 26, N190 15, N120 1, N150 6, E1N014 3 ;
- fallbacks techniques Mistral : 0 ; fallbacks exclus des metriques
  substantielles ;
- verification : toutes les sorties sont relues et validees par
  `validate_review_output_v2`.

### Bloc 4 - Controle qualite

- [x] Controler les faux positifs.
- [x] Controler les faux negatifs.
- [x] Controler les cas ambigus.
- [x] Documenter les limites et erreurs observees.

Note Bloc 4 - controle qualite Mistral V2 :

- sorties relues : 51 ; fallbacks techniques : 0 ; `is_fallback = true` absent.
- Absence de signal / faux positifs probables : 48 sorties
  `hors_perimetre / no_signal`, surtout des declencheurs lexicaux trop larges
  ou contextuels, plus l'echantillon neutre N190 : tensions politiques,
  mentions institutionnelles, groupes politiques caledoniens, prisons,
  occupation sans droit ni titre, elus locaux.
- Faux negatifs probables : aucun signal evident rate dans les sorties relues
  de N190, N120, N150 et E1N014 ; cette conclusion ne couvre pas les passages
  non relus hors candidats lexicaux, sauf l'echantillon neutre N190.
- Cas a revue humaine : 3 sorties N191 `adjacent / problematic_group_targeting`
  autour de `Kanaks`, `peuple kanak` et `anti-independantistes`. Elles sont
  plausibles comme signaux a revoir vu l'ancrage colonial et historique, mais
  restent fragiles : elles peuvent aussi relever de tension politique ou
  historique plutot que d'un ciblage problematique stabilise.
- Limite : controle documentaire court, sans verdict politique, sans nouvelle
  taxonomie et sans relance modele.

### Bloc 5 - Couts, volumes et cloture Phase C

- [x] Verifier les volumes relus sur le petit lot.
- [x] Verifier les couts du flux V2 sur le petit lot.
- [x] Declarer explicitement le critere de sortie de Phase C atteint ou non.

Note Bloc 5 - cloture Phase C :

- Decision : le critere de sortie de Phase C est atteint. La Phase C est
  cloturee ; le test sur petit lot est valide. Cela ne signifie pas que
  l'application finale est terminee.
- Volumes : 5 seances, 992 interventions structurees, 51 sorties Mistral V2
  relues ; N191 26, N190 15, N120 1, N150 6, E1N014 3 ; 0 fallback technique.
- Couts / appels : 51 appels Mistral V2 reels sur le lot. Le cout exact n'est
  pas chiffre dans la roadmap ; le volume reste borne pour Phase C et devra
  etre estime avant l'extension corpus complet.
- Valide : parsing du lot, exports V2 separes, validation contrat V2, resume
  Mistral V2, controle qualite court et exclusion des fallbacks techniques des
  metriques substantielles.
- Fragile : lot limite a cinq seances, peu de cas `adjacent`, dependance aux
  candidats lexicaux hors echantillon neutre N190, cout exact non mesure.
- Reporte a la Phase D : passage au corpus local complet, agregations
  multi-seances, estimation de cout a plus grande echelle et maintien des
  exclusions de fallbacks.

## Phase D - Corpus local complet

Statut : en cours.

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

1. Parser le corpus local Assemblee.
2. Produire les exports multi-seances.
3. Generer les agregations V2 en excluant `is_fallback = true` des metriques
   substantielles.

## Ne pas faire maintenant

- pas de D3 ;
- pas d'automatisation collecte ;
- pas de nouvelle taxonomie ;
- pas de refonte architecture ;
- pas d'application UI pendant la Phase D.

## Points de vigilance

- Ne pas elargir `core` a des tensions politiques ordinaires.
- Ne pas laisser `adjacent` devenir une categorie fourre-tout.
- Ne pas compter `is_fallback = true` comme un vrai hors-perimetre.
