# Plan contextualisation Assemblee

## Objectif

Ajouter une brique de relecture contextuelle des signaux candidats issus du pipeline Assemblee.

La brique aide a qualifier un passage candidat avant validation finale. Elle ne produit pas de verdict moral automatique.

## Place dans le workflow

Sequence visee :

1. Parser le XML pilote.
2. Produire les interventions enrichies.
3. Detecter les signaux candidats par regles.
4. Construire un contexte local pour chaque candidat.
5. Appeler un provider contextualisateur.
6. Valider la sortie agentique.
7. Preparer la revue humaine.

La brique intervient apres la detection rule-based et avant validation ou publication.

## Role de l'agent contextualisateur

- relire le passage candidat dans son contexte local ;
- distinguer un signal pertinent, un faux positif ou un cas ambigu ;
- produire une sortie JSON stricte ;
- aider la revue humaine ciblee ;
- signaler ses limites.

## Ce que la brique fait

- lit les interventions enrichies ;
- derive les candidats rule-based ;
- construit un payload de contexte local ;
- appelle un provider provider-agnostic ;
- valide la sortie du provider ;
- produit une revue agentique exploitable.

## Ce que la brique ne fait pas

- parser les XML bruts ;
- remplacer la detection rule-based ;
- modifier la timeline D3 ;
- lancer une recherche web par defaut ;
- conclure qu'un passage est raciste, discriminatoire ou haineux ;
- remplacer la revue humaine.

## Livrables attendus

- contrats d'entree et de sortie ;
- context builder minimal ;
- interface provider-agnostic ;
- provider mock stable ;
- reviewer minimal ;
- tests unitaires du squelette.

## Remis a plus tard

- choix d'un provider LLM reel ;
- prompt final ;
- batch complet sur corpus local ;
- reinjection dans la timeline ;
- scoring complexe ;
- recherche web optionnelle ;
- interface de validation humaine.
