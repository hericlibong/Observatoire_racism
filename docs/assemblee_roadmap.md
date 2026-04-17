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
- phases B, C, D et E cloturees : methode V2 stabilisee, petit lot teste,
  socle incremental simule et visualisation minimale disponible.

En cours :

- Phase F - Automatisation collecte et detection des nouvelles seances.

A faire :

- preparer la suite applicative apres stabilisation du flux incremental.

Explicitement remis a plus tard :

- Phase G - Application ;
- backfill complet du corpus historique local ;
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
  pas chiffre dans la roadmap ; le volume reste borne pour Phase C et confirme
  qu'il faut eviter un backfill historique massif sans besoin produit clair.
- Valide : parsing du lot, exports V2 separes, validation contrat V2, resume
  Mistral V2, controle qualite court et exclusion des fallbacks techniques des
  metriques substantielles.
- Fragile : lot limite a cinq seances, peu de cas `adjacent`, dependance aux
  candidats lexicaux hors echantillon neutre N190, cout exact non mesure.
- Reporte a la Phase D : socle incremental seance par seance,
  journalisation des traitements, exports de seance pour visualisation et
  maintien des exclusions de fallbacks. Le corpus historique local reste une
  reserve de test ou d'audit ponctuel, pas la phase active.

## Phase D - Socle incremental seance par seance

Statut : cloturee.

Objectif : preparer le processus qui traitera chaque nouvelle seance des
qu'elle sera disponible. Tant qu'aucune nouvelle seance n'existe localement,
le flux est teste sur une seance existante de simulation, sans backfill complet
du corpus historique local.

Taches :

- tenir un journal des seances traitees ;
- savoir constater qu'aucune nouvelle seance n'est encore disponible ;
- choisir explicitement une seance de simulation si necessaire ;
- parser une seance a la fois ;
- appliquer le flux V2 a la seance courante ;
- produire un export de seance exploitable par la visualisation ;
- journaliser le traitement pour eviter les doublons ;
- maintenir l'exclusion de `is_fallback = true` des metriques substantielles.

Critere de sortie :

- le flux fonctionne sur une seance unique existante utilisee comme simulation ;
- un journal de traitement indique ce qui a deja ete traite ;
- le systeme peut distinguer "nouvelle seance disponible" de "rien a traiter" ;
- l'export de seance est disponible pour la heatmap detaillee ;
- fallbacks exclus des metriques substantielles.

## Todo actif - Phase D

### Bloc 1 - Journal de traitement

- [x] Definir le format minimal du journal des seances traitees.
- [x] Prevoir les champs utiles : seance_id, fichier source, date de seance,
  date de traitement, provider, exports produits, statut, erreur eventuelle.
- [x] Decider ou stocker ce journal sans melanger avec les exports historiques.

Note Bloc 1 - journal de traitement :

- format retenu : JSONL, un enregistrement par seance traitee ;
- emplacement retenu : `data/interim/assemblee/processing_journal_v2.jsonl`,
  separe des exports historiques `contextual_reviews_*` et des exports D3 ;
- champs minimaux : `seance_id`, `source_file`, `seance_date`,
  `seance_date_label`, `processed_at`, `provider`, `model_name`, `status`,
  `outputs`, `fallback_count`, `reviewed_items`, `error` ;
- `seance_date` et `seance_date_label` viennent des metadonnees XML
  `dateSeance` et `dateSeanceJour` ; `processed_at` reste la date de traitement
  informatique ;
- `outputs` liste les chemins produits pour la seance ; `status` reste sobre,
  par exemple `success` ou `error` ;
- aucun fichier journal n'etait encore cree au Bloc 1 : il est alimente lors du
  premier vrai traitement incremental ou de la seance de simulation.

### Bloc 2 - Detection de nouvelle seance ou simulation

- [x] Identifier la derniere seance locale disponible et l'etat du journal.
- [x] Constater explicitement si aucune nouvelle seance n'est disponible.
- [x] Choisir une seance existante de simulation seulement si necessaire.
- [x] Documenter la regle de selection sans backfill complet.

Note Bloc 2 - detection incremental / simulation :

- derniere seance locale disponible : `CRSANR5L17S2026O1N191.xml`, presente
  dans `data/raw/assemblee/extracted/syceron_initial_import/syseron.xml/xml/compteRendu/` ;
- etat du journal : `data/interim/assemblee/processing_journal_v2.jsonl`
  absent ; aucun traitement incremental n'est encore journalise. Les exports
  N191 existants restent des sorties de test historiques ou Phase C, pas des
  entrees du journal ;
- conclusion : aucune nouvelle seance reelle plus recente que N191 n'est
  disponible localement ; ne pas inventer de N192 ;
- simulation retenue : N191, car c'est la derniere seance locale disponible et
  une reference deja connue ;
- regle : traiter uniquement la seance explicitement choisie pour simulation ou
  la prochaine nouvelle seance reelle ; ne pas faire de backfill complet.

### Bloc 3 - Traitement d'une seance unique

- [x] Parser uniquement la seance retenue.
- [x] Appliquer le flux V2 a cette seance.
- [x] Produire un export V2 dedie a cette seance.
- [x] Verifier que `is_fallback = true` reste exclu des metriques
  substantielles.

Note Bloc 3 - traitement N191 simulation :

- seance traitee : `CRSANR5L17S2026O1N191.xml`, comme simulation
  incrementale, pas comme nouvelle seance reelle ;
- commande : `python -m src.assemblee_contextualization.run_pilot_v2 --provider mistral --source-file CRSANR5L17S2026O1N191.xml --output data/interim/assemblee/contextual_reviews_phase_d_simulation_n191_v2_mistral.jsonl --summary-output data/interim/assemblee/contextual_reviews_phase_d_simulation_n191_v2_mistral_summary.json` ;
- export : `data/interim/assemblee/contextual_reviews_phase_d_simulation_n191_v2_mistral.jsonl` ;
- resume : `data/interim/assemblee/contextual_reviews_phase_d_simulation_n191_v2_mistral_summary.json` ;
- sorties V2 : 26 ; fallbacks techniques : 0 ;
- validation : toutes les sorties sont relues par `read_outputs_v2` et passent
  `validate_review_output_v2` ; les metriques substantielles excluent les
  fallbacks ;
- journal : `data/interim/assemblee/processing_journal_v2.jsonl` n'a pas ete
  cree au Bloc 3 ; la journalisation releve du Bloc 4.

### Bloc 4 - Journalisation et non-duplication

- [x] Enregistrer le traitement dans le journal.
- [x] Verifier qu'une seance deja traitee n'est pas relancee par defaut.
- [x] Documenter les erreurs ou fallbacks eventuels.

Note Bloc 4 - journalisation N191 simulation :

- journal cree : `data/interim/assemblee/processing_journal_v2.jsonl` ;
- entree ajoutee : `CRSANR5L17S2026O1N191`, date de seance `2026-04-02`
  (`jeudi 02 avril 2026`), statut `success`, provider `mistral_v2`, modele
  `mistral-medium-latest`, 26 sorties relues, 0 fallback technique,
  `error` vide ;
- outputs journalises :
  `data/interim/assemblee/contextual_reviews_phase_d_simulation_n191_v2_mistral.jsonl`
  et
  `data/interim/assemblee/contextual_reviews_phase_d_simulation_n191_v2_mistral_summary.json` ;
- non-duplication : `is_seance_already_processed("CRSANR5L17S2026O1N191")`
  retourne `true` ; une seance absente du journal, par exemple N192, retourne
  `false` ;
- limite : le journal marque la simulation N191 comme traitement incremental
  reussi ; les exports historiques N191 ne sont pas convertis en entrees du
  journal.

### Bloc 5 - Export pour visualisation seance

- [x] Produire ou definir l'export necessaire a la heatmap intra-seance.
- [x] Prevoir les champs utiles au clic detail : ordre, extrait, categorie,
  niveau de perimetre, besoin de revue humaine.
- [x] Garder la visualisation prudente : signal a revoir, jamais verdict.

Note Bloc 5 - export heatmap seance :

- decision : l'export V2 Phase D seul ne suffit pas pour la heatmap, car il ne
  contient pas l'axe interne de seance ni les champs de clic detail ; une
  transformation minimale est donc creee ;
- export produit : `data/interim/assemblee/heatmap_session_n191_v2.json` ;
- source : `contextual_reviews_phase_d_simulation_n191_v2_mistral.jsonl`,
  `contextual_reviews_phase_d_simulation_n191_v2_mistral_summary.json` et
  `processing_journal_v2.jsonl`, avec parsing local de N191 pour les metadonnees
  d'intervention ;
- contenu : 26 items, axe `ordre` de 13 a 260, champs `seance_id`,
  `source_file`, `seance_date`, `seance_date_label`, `ordre`,
  `intervention_id`, `orateur_nom`, `point_titre`, `sous_point_titre`,
  `excerpt`, `evidence_span`, `scope_level`, `signal_category`, `confidence`,
  `needs_human_review`, `is_fallback` ;
- prudence : libelles `signal a revoir` / `aucun signal a revoir`, jamais
  verdict automatique ;
- fallbacks : 0 dans l'export N191 ; la structure garde les fallbacks visibles
  mais les exclut des metriques substantielles.

### Bloc 6 - Cloture Phase D

- [x] Verifier que le flux fonctionne sur une seance unique de simulation.
- [x] Lister ce qui est valide, fragile et reporte.
- [x] Declarer explicitement le critere de sortie de Phase D atteint ou non.

Note Bloc 6 - cloture Phase D :

- Decision : le critere de sortie de Phase D est atteint. La Phase D est
  cloturee ; la prochaine phase active devient la Phase E. Cela ne lance pas le
  travail de visualisation.
- Valide : N191 traitee comme simulation unique, 26 sorties V2 Mistral
  validees, 0 fallback technique, resume Phase D disponible, journal JSONL cree
  avec date de seance et date de traitement distinctes, non-duplication
  detectable, export heatmap seance produit.
- Fallbacks : exclus des metriques substantielles dans le resume V2 et dans
  l'export heatmap ; aucun fallback technique observe sur N191.
- Fragile : validation sur une seule seance de simulation, pas encore sur une
  nouvelle seance reelle ; la detection automatisee des nouvelles seances reste
  hors Phase D ; dans l'export heatmap, `substantive_items` signifie aujourd'hui
  "items non fallback".
- Reporte : visualisation heatmap et vue inter-seances en Phase E ; collecte et
  detection automatisees en Phase F ; avant la visualisation, envisager un nom
  plus clair comme `non_fallback_items`.

## Phase D optionnelle - Reserve d'audit historique

Statut : optionnelle.

Objectif : utiliser les anciennes seances locales comme reserve de test,
d'audit ponctuel ou de regression, sans backfill complet.

Taches eventuelles :

- selectionner un petit echantillon cible si un doute methodologique apparait ;
- comparer une sortie recente a quelques cas historiques de controle ;
- ne jamais confondre cette reserve avec le flux vivant de production.

## Phase E - Visualisation heatmap seance et suivi inter-seances

Statut : cloturee pour socle minimal.

Objectif : afficher d'abord une heatmap detaillee d'une seance, puis une vue
generale inter-seances.

Taches :

- construire la vue detaillee d'une seance : axe interne, densite / presence de
  signaux, clic vers les passages ;
- construire ensuite la vue generale : une case ou un segment par seance / jour
  de seance, clic vers la vue detaillee ;
- choisir les champs V2 a afficher prudemment ;
- verifier que la visualisation ne produit pas de verdict.

Critere de sortie :

- heatmap detaillee par seance exploitable ;
- vue generale inter-seances minimale ;
- absence de formulation ou codage visuel assimilable a un verdict.

## Todo actif - Phase E

### Bloc 1 - Contrat visuel minimal de la heatmap seance

- [x] Definir ce que represente l'axe interne de seance.
- [x] Definir ce que represente la couleur.
- [x] Definir les libelles prudents : signal a revoir, jamais verdict.
- [x] Clarifier `substantive_items` / `non_fallback_items` avant affichage.

Note Bloc 1 - contrat visuel minimal heatmap seance :

- Source de travail : `data/interim/assemblee/heatmap_session_n191_v2.json`,
  26 items, 0 fallback, axe `ordre` de 13 a 260.
- Axe interne : utiliser `ordre` comme position canonique ; `axis_position`
  peut servir de duplicat technique si besoin. L'utilisateur doit comprendre un
  deroulement ordonne dans la seance, pas un temps chronometrique ni une duree.
  Une normalisation visuelle eventuelle ne change pas ce sens.
- Couleur : coder un niveau de revue prudent, jamais une culpabilite, une
  gravite morale ou un verdict. Proposition : `hors_perimetre / no_signal`
  neutre ; `adjacent` teinte de revue moderee ; `core` teinte de revue plus
  visible ; `is_fallback = true` teinte technique separee, hors metriques
  substantielles.
- Libelles : afficher `aucun signal a revoir`, `signal a revoir` ou
  `passage a revoir` ; interdire `signal valide`, `propos raciste`,
  `haine detectee` et formulations equivalentes.
- Vocabulaire : dans l'export actuel, `substantive_items` signifie "items non
  fallback". Avant affichage, preferer un libelle ou un alias plus clair :
  `non_fallback_items`. Pas de changement de code dans ce bloc.

### Bloc 2 - Preparation des donnees de visualisation

- [x] Verifier ou ajuster `heatmap_session_n191_v2.json`.
- [x] Verifier les champs necessaires au clic detail.
- [x] Garder les fallbacks visibles mais exclus des metriques substantielles.
- [x] Ne pas relancer Mistral.

Note Bloc 2 - donnees heatmap seance :

- export verifie et regenere : `data/interim/assemblee/heatmap_session_n191_v2.json` ;
- decision vocabulaire : ajout de `non_fallback_items` dans `metrics` et
  conservation temporaire de `substantive_items` comme alias pour eviter une
  rupture inutile ;
- champs verifies : `session` contient `seance_id`, `source_file`,
  `seance_date`, `seance_date_label`, `processed_at`, `provider`,
  `model_name` ; `axis` contient `field`, `min`, `max`, `reviewed_items` ;
  `items` contient les champs necessaires au clic detail, dont `ordre`,
  `axis_position`, `intervention_id`, `orateur_nom`, `point_titre`,
  `sous_point_titre`, `excerpt`, `evidence_span`, `scope_level`,
  `signal_category`, `confidence`, `needs_human_review`, `is_fallback`,
  `review_label` ;
- fallbacks : visibles dans `items` via `is_fallback`, mais exclus de
  `non_fallback_items` ; N191 contient 0 fallback ;
- libelles : `aucun signal a revoir` et `signal a revoir`, sans verdict
  automatique.

### Bloc 3 - Vue detaillee d'une seance

- [x] Creer ou adapter une heatmap / timeline pour une seule seance.
- [x] Utiliser N191 comme seance de simulation.
- [x] Prevoir un clic ou une interaction vers les details des passages.
- [x] Ne jamais afficher de verdict automatique.

Note Bloc 3 - vue detaillee seance N191 :

- decision : creation d'une vue dediee Phase E, plutot qu'adaptation du pilote
  historique, pour eviter la confusion entre l'ancien flux lexical et l'export
  heatmap V2 ;
- fichiers : `data/exports/d3/assemblee_session_heatmap_n191.html` et
  `data/exports/d3/assemblee_session_heatmap_n191.json` ;
- source : `data/interim/assemblee/heatmap_session_n191_v2.json` ;
- axe : `axis_position` / `ordre`, lu comme ordre de deroulement dans la seance,
  pas comme duree chronometrique ;
- couleur : `hors_perimetre / no_signal` neutre, `adjacent` revue moderee,
  `core` passage a revoir plus visible, fallback technique separe ;
- interaction : clic, survol ou clavier sur une marque pour afficher ordre,
  orateur, point / sous-point, extrait, `evidence_span`, `scope_level`,
  `signal_category`, `confidence`, `review_label`, `needs_human_review` et
  `is_fallback` ;
- prudence : libelles de type `signal a revoir`, `passage a revoir`,
  `aucun signal a revoir`, `fallback technique a revoir`, sans verdict
  automatique.

### Bloc 4 - Vue generale inter-seances minimale

- [x] Definir une structure minimale de listing inter-seances.
- [x] Utiliser uniquement les seances journalisees ou les exports disponibles.
- [x] Prevoir un lien conceptuel vers la vue detaillee.
- [x] Ne pas traiter tout le corpus historique.

Note Bloc 4 - vue generale inter-seances minimale :

- premiere proposition : un export de listing `data/exports/d3/assemblee_sessions_overview.json`
  et une vue D3 tabulaire simple `data/exports/d3/assemblee_sessions_overview.html` ;
- variante testee : heatmap inter-seances minimale a un carre, N191 seule
  pour l'instant ; decision finale a arbitrer apres evaluation visuelle ;
- source : uniquement `data/interim/assemblee/processing_journal_v2.jsonl` et
  l'export detaille disponible `data/exports/d3/assemblee_session_heatmap_n191.json` ;
- contenu actuel : une seance disponible, N191, avec 26 passages relus,
  26 analyses disponibles hors fallback, 24 passages "rien a signaler ici",
  2 passages "a lire avec prudence", 0 "important pour l'observatoire" et
  0 analyse non disponible ;
- lien : le carre N191 renvoie vers
  `data/exports/d3/assemblee_session_heatmap_n191.html` ;
- limite volontaire : aucun backfill du corpus historique, aucune relance
  Mistral, aucun changement du flux V2, des providers ou de la taxonomie.

### Bloc 5 - Verification editoriale et cloture Phase E

- [x] Verifier la prudence des libelles.
- [x] Verifier que `is_fallback = true` n'est pas compte comme signal substantiel.
- [x] Lister ce qui est valide, fragile et reporte.
- [x] Declarer explicitement le critere de sortie de Phase E atteint ou non.

Note Bloc 5 - verification editoriale et cloture Phase E :

- verification : les vues `data/exports/d3/assemblee_session_heatmap_n191.html`
  et `data/exports/d3/assemblee_sessions_overview.html` chargent leurs JSON
  respectifs ; les scripts embarques passent `node --check` ; aucun vocabulaire
  de verdict ou d'accusation n'a ete releve dans les interfaces HTML ;
- fallback : `is_fallback = true` reste distinct des signaux substantiels ;
  dans N191, `non_fallback_items = reviewed_items - fallback_count` et le
  nombre de fallbacks observe dans `items` est coherent avec `metrics` ; dans
  la vue inter-seances, `available_analyses = reviewed_items - fallback_count`
  et les signaux affiches restent inferieurs ou egaux aux analyses disponibles ;
- critere de sortie Phase E : atteint pour un socle minimal exploitable, non
  pour un design public final.

Valide :

- vue detaillee N191 exploitable ;
- vue inter-seances minimale exploitable ;
- navigation entre vue inter-seances et vue detaillee N191 ;
- prudence editoriale maintenue ;
- pas de verdict automatique ;
- fallback technique distinct des signaux substantiels.

Fragile :

- une seule seance disponible dans la vue inter-seances ;
- design encore provisoire ;
- legendes encore a ameliorer ;
- style difficile a maintenir ;
- navigation vers une page detail qui pourra etre remplacee plus tard.

Reporte :

- consolidation visuelle ;
- storytelling public ;
- legendes heatmap plus lisibles ;
- integration du detail sous la timeline principale en panneau ou slide ;
- amelioration du style quand plusieurs seances seront disponibles ;
- Phase F pour automatisation collecte / nouvelles seances.

Note design a completer : la Phase E valide le socle fonctionnel de
visualisation, mais le design public reste a consolider ulterieurement
avant une mise en forme finale.

## Phase F - Automatisation collecte et detection des nouvelles seances

Statut : en cours.

Objectif : automatiser l'arrivee des nouveaux XML qui alimenteront le flux
incremental de la Phase D.

Taches :

- identifier la source de collecte ;
- detecter qu'une nouvelle seance est disponible apres la derniere seance
  journalisee ;
- automatiser le telechargement ou l'import du XML ;
- eviter les doublons ;
- mettre a jour le manifest ;
- preparer le declenchement du traitement incremental.

Critere de sortie :

- collecte reproductible ;
- manifest mis a jour ;
- une nouvelle seance peut etre detectee et mise a disposition du flux Phase D.

## Todo actif - Phase F

### Bloc 1 - Cadrage de la source de collecte

- [x] Identifier la source a utiliser pour recuperer les nouveaux XML.
- [x] Distinguer clairement source distante, cache local et fichiers deja
  extraits.
- [x] Definir les informations minimales a conserver pour chaque XML candidat.
- [x] Documenter les limites : pas de backfill complet, pas de traitement V2
  automatique dans ce bloc.

Critere de sortie Bloc 1 :

- une source de collecte est retenue ou, a defaut, une strategie temporaire
  d'import local est documentee ;
- les champs minimaux de suivi sont listes avant implementation.

Note Bloc 1 - cadrage collecte :

- source retenue : source officielle Assemblee nationale
  `https://data.assemblee-nationale.fr/static/openData/repository/17/vp/syceronbrut/syseron.xml.zip`,
  archive ZIP complete `syseron.xml.zip`, consideree comme source brute
  officielle pour les comptes rendus XML ;
- constat local : un cache ZIP existe deja dans `data/raw/assemblee/zips/` ;
  les XML deja extraits sont actuellement sous
  `data/raw/assemblee/extracted/syceron_initial_import/syseron.xml/xml/compteRendu`,
  chemin repris par `SOURCE_DIR` dans `src/build_assemblee_pilot.py` ; un
  `data/interim/assemblee/source_manifest.json` existe deja et le journal
  `data/interim/assemblee/processing_journal_v2.jsonl` contient N191 comme
  seance traitee ;
- separation des espaces : source distante officielle ; archive telechargee ou
  cache local ; XML extraits localement ; manifest de disponibilite ; journal
  de traitement V2 ;
- initialisation ponctuelle : importer ou inventorier une seule fois toutes les
  seances disponibles avec `dateSeance >= 2026-04-02` ; inclure
  `CRSANR5L17S2026O1N191.xml`, date `2026-04-02`, point d'ancrage deja utilise
  en simulation Phase D et visualisation Phase E ; ne pas backfiller le flux
  actif avant le 2 avril 2026 ;
- regime courant apres initialisation : verifier la source officielle, detecter
  la derniere seance disponible, comparer avec le manifest et le journal local,
  recuperer uniquement les seances absentes, et rester capable d'identifier
  plusieurs nouvelles seances si plusieurs publications arrivent depuis le
  dernier passage ;
- champs minimaux a conserver pour chaque XML candidat : `source_url`,
  `archive_name`, `source_file`, `seance_id`, `seance_date`,
  `seance_date_label`, `local_path`, `content_hash`, `available_status`,
  `already_processed`, `journal_status` ;
- role du manifest : decrire les XML disponibles localement ou detectes, savoir
  ce qui existe et ce qui est candidat au traitement ; il ne signifie pas que
  le flux V2 a ete lance ;
- role du journal : decrire les seances effectivement traitees par le flux V2,
  eviter les doublons de traitement, conserver exports produits, statuts,
  erreurs et compteurs ;
- limite du bloc : aucun telechargement implemente, aucun traitement XML, aucune
  relance Mistral, aucune modification du pipeline V2, des providers, de D3 ou
  des exports.

### Bloc 2 - Inventaire local et etat du journal

- [x] Lire les XML deja disponibles localement.
- [x] Lire `data/interim/assemblee/processing_journal_v2.jsonl` si present.
- [x] Identifier la derniere seance locale disponible.
- [x] Identifier la derniere seance traitee dans le journal.
- [x] Savoir conclure explicitement : nouvelle seance disponible ou rien a
  traiter.

Critere de sortie Bloc 2 :

- une commande ou fonction peut produire un etat sec : dernier XML local,
  dernier traitement journalise, prochaine seance candidate ou absence de
  nouveaute.

Note Bloc 2 - inventaire local et etat du journal :

- capacite ajoutee : `src/assemblee_contextualization/source_inventory.py`,
  independante des providers et du flux V2, avec `build_local_inventory_status`
  pour produire un etat sec ;
- chemin des XML locaux : `data/raw/assemblee/extracted/syceron_initial_import/syseron.xml/xml/compteRendu`,
  via `SOURCE_DIR` existant ;
- date seuil appliquee : `dateSeance >= 2026-04-02` ;
- journal lu si present : `data/interim/assemblee/processing_journal_v2.jsonl` ;
- derniere seance locale detectee : `CRSANR5L17S2026O1N191.xml`,
  date `2026-04-02`, libelle `jeudi 02 avril 2026` ;
- derniere seance journalisee : `CRSANR5L17S2026O1N191`, statut `success` ;
- conclusion actuelle : aucune nouvelle seance a traiter, car aucune seance
  locale filtree n'est absente du journal de traitement ;
- limites : aucun telechargement, aucun appel reseau, aucun manifest modifie,
  aucun traitement XML complet, aucune relance Mistral et aucun lancement du
  flux V2 dans ce bloc.

### Bloc 3 - Import ou telechargement minimal d'un XML

- [x] Definir le mode d'acquisition minimal : telechargement si source distante
  stabilisee, sinon import local controle.
- [x] Stocker le XML dans l'arborescence raw existante sans casser les chemins
  actuels.
- [x] Eviter les doublons par nom de fichier et, si possible, par empreinte de
  contenu.
- [x] Verifier que le XML importe est lisible par le parseur Assemblee existant.
- [x] Ne pas lancer Mistral ni le flux V2 dans ce bloc.

Critere de sortie Bloc 3 :

- un nouveau fichier XML peut etre ajoute ou simule proprement dans le stock
  local, sans doublon et sans traitement automatique.

Note Bloc 3 - import XML minimal :

- mode retenu pour ce bloc : import local controle, avec extraction ciblee
  possible depuis l'archive ZIP locale deja presente ;
- archive d'entree locale : `data/raw/assemblee/zips/syseron.xml.zip` ;
- destination XML conservee : `data/raw/assemblee/extracted/syceron_initial_import/syseron.xml/xml/compteRendu`,
  afin de ne pas casser `SOURCE_DIR` ni les chemins Phase D/E ;
- brique ajoutee : `src/assemblee_contextualization/source_acquisition.py`,
  independante des providers, du flux V2, de D3, du manifest et du journal ;
- regle anti-doublon : meme nom de fichier et meme SHA-256 dans la destination
  signifie deja present, sans recopie ni traitement ;
- regle de conflit : meme nom de fichier mais SHA-256 different bloque
  l'import par defaut ; `overwrite=True` est requis pour remplacer
  explicitement ;
- validation XML : fichier parseable, racine `compteRendu` dans le namespace
  Assemblee attendu, `uid`, `dateSeance`, `dateSeanceJour` et `contenu`
  presents ;
- limite du bloc : aucun telechargement distant execute, aucun manifest genere
  ou modifie, aucun journal modifie, aucune relance Mistral et aucun lancement
  du flux V2.

### Bloc 4 - Manifest de disponibilite

- [x] Clarifier le role de `source_manifest.json` par rapport au journal de
  traitement.
- [x] Mettre a jour ou produire un manifest des XML disponibles.
- [x] Ajouter les champs necessaires : `source_file`, `seance_id`,
  `seance_date`, chemin local, statut de disponibilite, empreinte si retenue.
- [x] Distinguer disponible, deja traite, ignore et erreur d'import.
- [x] Garder le manifest separe des exports V2 et des exports D3.

Critere de sortie Bloc 4 :

- le manifest permet de savoir quels XML existent localement et lesquels
  restent candidats au traitement incremental.

Note Bloc 4 - manifest de disponibilite :

- manifest produit : `data/interim/assemblee/source_manifest.json` ;
- brique ajoutee : `src/assemblee_contextualization/source_manifest.py`, qui
  lit l'archive locale, materialise les XML retenus dans le stock raw si
  necessaire, puis ecrit le manifest sans declencher de traitement V2 ;
- collecte distante reelle executee depuis la source officielle Assemblee
  nationale ; le ZIP local `data/raw/assemblee/zips/syseron.xml.zip` a ete
  mis a jour avant regeneration du manifest ;
- brique de telechargement ajoutee dans
  `src/assemblee_contextualization/source_acquisition.py` : ecriture atomique,
  validation ZIP, comparaison de hash, statut `downloaded`, `updated` ou
  `unchanged` ;
- regle de seuil : seules les seances avec `dateSeance >= 2026-04-02` sont
  retenues dans le manifest actif ; les XML anterieurs sont ignores par filtre
  et ne sont pas backfilles ;
- resultat apres collecte distante : 486 XML comptes rendus vus dans l'archive,
  471 ignores avant seuil, 15 seances detectees depuis le seuil ;
- seance d'ancrage : `CRSANR5L17S2026O1N191.xml`, `2026-04-02`, deja traitee
  mais marquee en conflit de contenu car l'archive distante actualisee differe
  du XML local deja journalise ; aucun ecrasement automatique n'est effectue ;
- nouvelles seances materialisees depuis le ZIP : 14, de
  `CRSANR5L17S2026O1N192.xml` a `CRSANR5L17S2026O1N205.xml` ;
- journal V2 : 1 seance deja traitee, `CRSANR5L17S2026O1N191`, statut
  `success` ;
- candidates au traitement : 14, `CRSANR5L17S2026O1N192.xml`,
  `CRSANR5L17S2026O1N193.xml`, `CRSANR5L17S2026O1N194.xml`,
  `CRSANR5L17S2026O1N195.xml`, `CRSANR5L17S2026O1N196.xml`,
  `CRSANR5L17S2026O1N197.xml`, `CRSANR5L17S2026O1N198.xml`,
  `CRSANR5L17S2026O1N199.xml`, `CRSANR5L17S2026O1N200.xml`,
  `CRSANR5L17S2026O1N201.xml`, `CRSANR5L17S2026O1N202.xml`,
  `CRSANR5L17S2026O1N203.xml`, `CRSANR5L17S2026O1N204.xml`,
  `CRSANR5L17S2026O1N205.xml` ;
- role du manifest : dire quels XML existent et sont disponibles localement,
  avec hash et statut de disponibilite ; role du journal : dire quelles seances
  ont reellement ete traitees par V2 ; le manifest ne declenche aucun
  traitement ;
- absence de traitement V2 : aucune relance Mistral, aucun run incremental,
  aucun export V2 ou D3 produit dans ce bloc.

Dette structurelle Phase F :

- le package `assemblee_contextualization` regroupe maintenant collecte,
  acquisition, inventaire, manifest, journal, contextualisation et
  visualisation ; ne pas refactoriser pendant la Phase F, mais prevoir un
  rangement leger apres cloture pour separer les briques collecte/source des
  briques contextualisation et visualisation.

### Bloc 5 - Passerelle vers le flux incremental

- [x] Preparer la selection de la prochaine seance a traiter a partir du
  manifest et du journal.
- [x] Produire une commande ou un point d'entree qui passe explicitement la
  seance candidate au flux V2 existant.
- [x] Conserver un mode de verification sans appel modele avant execution
  reelle.
- [x] Garantir que les doublons journalises ne sont pas relances par defaut.
- [x] Ne pas modifier le contrat V2, les providers ou la taxonomie.

Critere de sortie Bloc 5 :

- une nouvelle seance disponible peut etre transmise au flux incremental de
  maniere controlee, avec garde-fou contre les relances involontaires.

Note Bloc 5 - passerelle incremental V2 :

- workflow retenu : traitement incremental seance par seance, jamais en batch
  automatique sur toutes les candidates ;
- point d'entree ajoute : `src/assemblee_contextualization/run_incremental_session_v2.py`,
  avec selection explicite par `--source-file`, mode `--dry-run` sans appel
  provider, et execution reelle uniquement avec `--confirm` ;
- premiere candidate traitee : `CRSANR5L17S2026O1N192.xml`, date
  `2026-04-07`, disponible dans le manifest, non journalisee avant execution ;
- dry-run execute sur N192 : statut `available`, `already_processed=false`,
  `journal_status=not_processed`, exports prevus
  `data/interim/assemblee/contextual_reviews_incremental_n192_v2_mistral.jsonl`
  et
  `data/interim/assemblee/contextual_reviews_incremental_n192_v2_mistral_summary.json`,
  sans appel Mistral ni traitement V2 ;
- traitement reel execute explicitement sur N192 avec provider `mistral` et
  `--confirm` ; aucune autre candidate n'a ete traitee ;
- exports produits :
  `data/interim/assemblee/contextual_reviews_incremental_n192_v2_mistral.jsonl`
  et
  `data/interim/assemblee/contextual_reviews_incremental_n192_v2_mistral_summary.json` ;
- journal mis a jour dans `data/interim/assemblee/processing_journal_v2.jsonl`
  avec une entree `success` pour `CRSANR5L17S2026O1N192`, provider
  `mistral_v2`, modele `mistral-medium-latest`, 4 sorties relues, 0 fallback,
  `error=""` ;
- verification post-traitement : N192 est refusee a la relance par defaut car
  deja journalisee ; le manifest regenere indique 13 candidates restantes, de
  `CRSANR5L17S2026O1N193.xml` a `CRSANR5L17S2026O1N205.xml` ;
- N191 n'est pas relancee : elle reste refusee par la passerelle car son statut
  manifest est `conflict` et elle est deja journalisee ;
- contrat V2, providers, taxonomie, D3 et exports de visualisation inchanges.

Note de continuite visualisation post-traitement N192 :

- N192 dispose maintenant d'une vue D3 de detail :
  `data/exports/d3/assemblee_session_heatmap_n192.html`, alimentee par
  `data/exports/d3/assemblee_session_heatmap_n192.json` et par l'export
  intermediaire `data/interim/assemblee/heatmap_session_n192_v2.json` ;
- la heatmap inter-seances `data/exports/d3/assemblee_sessions_overview.html`
  affiche desormais N191 et N192, chacune liee a sa vue de detail ;
- N193 a N205 restent candidates dans le manifest mais ne sont pas visualisees
  dans l'overview tant qu'elles ne sont pas traitees et ne disposent pas d'une
  vue detaillee ;
- le design D3 reste provisoire et sera consolide plus tard ;
- aucune relance Mistral, aucun traitement N193-N205, aucun changement du
  contrat V2, des providers ou de la taxonomie n'a ete effectue pour cette
  etape.

Note de continuite Bloc 5 - workflow complet N193 :

- N193 a ete traitee dans le workflow incremental seance par seance :
  `CRSANR5L17S2026O1N193.xml`, date `2026-04-07` ;
- dry-run execute sur N193 : statut `available`, `already_processed=false`,
  `journal_status=not_processed`, exports prevus
  `data/interim/assemblee/contextual_reviews_incremental_n193_v2_mistral.jsonl`
  et
  `data/interim/assemblee/contextual_reviews_incremental_n193_v2_mistral_summary.json`,
  sans appel Mistral ni ecriture d'export ;
- traitement reel execute explicitement sur N193 avec provider `mistral` et
  `--confirm` ; aucune autre candidate n'a ete traitee ;
- exports V2 produits :
  `data/interim/assemblee/contextual_reviews_incremental_n193_v2_mistral.jsonl`
  et
  `data/interim/assemblee/contextual_reviews_incremental_n193_v2_mistral_summary.json` ;
- journal mis a jour dans `data/interim/assemblee/processing_journal_v2.jsonl`
  avec une entree `success` pour `CRSANR5L17S2026O1N193`, provider
  `mistral_v2`, modele `mistral-medium-latest`, 13 sorties relues, 0 fallback,
  `error=""` ;
- manifest regenere : N193 est refusee a la relance par defaut car deja
  journalisee ; N194 a N205 restent candidates ;
- N193 dispose maintenant d'une vue D3 de detail :
  `data/exports/d3/assemblee_session_heatmap_n193.html`, alimentee par
  `data/exports/d3/assemblee_session_heatmap_n193.json` et par l'export
  intermediaire `data/interim/assemblee/heatmap_session_n193_v2.json` ;
- la heatmap inter-seances `data/exports/d3/assemblee_sessions_overview.html`
  affiche desormais uniquement N191, N192 et N193, chacune liee a sa vue de
  detail ;
- N194 a N205 restent non traitees et non visualisees dans l'overview tant
  qu'elles ne disposent pas d'une vue detaillee ;
- aucune refonte design, aucun changement du contrat V2, des providers ou de
  la taxonomie n'a ete lance.

Note de correction Bloc 5 - overview inter-seances :

- la vue inter-seances a ete corrigee apres integration N193 : N192 et N193
  partagent la date `2026-04-07`, ce qui provoquait une superposition visuelle
  avec la disposition precedente fondee sur la date comme position x ;
- `data/exports/d3/assemblee_sessions_overview.json` contient bien N191, N192
  et N193, chacune avec son lien vers la vue detaillee correspondante ;
- `data/exports/d3/assemblee_sessions_overview.html` utilise maintenant une
  disposition heatmap sequentielle compacte : une cellule par seance traitee,
  cellules rapprochees, date conservee comme libelle d'axe ;
- N194 a N205 restent absentes de l'overview car elles ne sont pas encore
  traitees et ne disposent pas d'une vue detaillee ;
- le design final de la heatmap inter-seances reste reporte.

### Bloc 6 - Verification et cloture Phase F

- [ ] Tester le cas "aucune nouvelle seance".
- [ ] Tester le cas "nouveau XML disponible mais non traite".
- [ ] Tester le cas "XML deja journalise".
- [ ] Verifier que le manifest et le journal restent coherents.
- [ ] Lister ce qui est valide, fragile et reporte.
- [ ] Declarer explicitement le critere de sortie de Phase F atteint ou non.

Critere de sortie Bloc 6 :

- la collecte ou l'import est reproductible ;
- le manifest est coherent avec le journal ;
- une nouvelle seance peut etre detectee et mise a disposition du flux Phase D
  sans backfill complet.

## Phase G - Application

Statut : remis a plus tard.

Objectif : passer des scripts a une application utilisable.

Taches :

- definir l'interface minimale ;
- definir le mode d'acces aux donnees ;
- brancher les exports stabilises ;
- decider ce qui est interne et ce qui est publiable.

## Prochaines taches immediates

1. Preparer la selection controlee de la prochaine seance candidate a traiter,
   a partir du manifest et du journal.
2. Tester le mode de verification sans appel modele sur les candidates N192 a
   N205.
3. Definir le garde-fou qui empeche de relancer par defaut N191 deja
   journalisee, surtout en presence du conflit de contenu detecte.

## Ne pas faire maintenant

- pas de backfill complet du corpus historique local ;
- pas de nouvelle taxonomie ;
- pas de refonte architecture ;
- pas d'application UI complete pendant la Phase F.

## Points de vigilance

- Ne pas elargir `core` a des tensions politiques ordinaires.
- Ne pas laisser `adjacent` devenir une categorie fourre-tout.
- Ne pas compter `is_fallback = true` comme un vrai hors-perimetre.
