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

- Phase E - Visualisation heatmap seance et suivi inter-seances.

A faire :

- Phase F - Automatisation collecte et detection des nouvelles seances.

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

Statut : en cours.

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

- [ ] Creer ou adapter une heatmap / timeline pour une seule seance.
- [ ] Utiliser N191 comme seance de simulation.
- [ ] Prevoir un clic ou une interaction vers les details des passages.
- [ ] Ne jamais afficher de verdict automatique.

### Bloc 4 - Vue generale inter-seances minimale

- [ ] Definir une structure minimale de listing inter-seances.
- [ ] Utiliser uniquement les seances journalisees ou les exports disponibles.
- [ ] Prevoir un lien conceptuel vers la vue detaillee.
- [ ] Ne pas traiter tout le corpus historique.

### Bloc 5 - Verification editoriale et cloture Phase E

- [ ] Verifier la prudence des libelles.
- [ ] Verifier que `is_fallback = true` n'est pas compte comme signal substantiel.
- [ ] Lister ce qui est valide, fragile et reporte.
- [ ] Declarer explicitement le critere de sortie de Phase E atteint ou non.

## Phase F - Automatisation collecte et detection des nouvelles seances

Statut : a faire.

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

## Phase G - Application

Statut : remis a plus tard.

Objectif : passer des scripts a une application utilisable.

Taches :

- definir l'interface minimale ;
- definir le mode d'acces aux donnees ;
- brancher les exports stabilises ;
- decider ce qui est interne et ce qui est publiable.

## Prochaines taches immediates

1. Definir le contrat visuel minimal de la heatmap seance a partir de
   `heatmap_session_n191_v2.json`.
2. Construire la vue detaillee d'une seance sans verdict automatique.
3. Preparer ensuite la vue generale inter-seances.

## Ne pas faire maintenant

- pas de backfill complet du corpus historique local ;
- pas d'automatisation collecte ;
- pas de nouvelle taxonomie ;
- pas de refonte architecture ;
- pas d'application UI complete pendant la Phase E.

## Points de vigilance

- Ne pas elargir `core` a des tensions politiques ordinaires.
- Ne pas laisser `adjacent` devenir une categorie fourre-tout.
- Ne pas compter `is_fallback = true` comme un vrai hors-perimetre.
