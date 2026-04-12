# Plan contextualisation Assemblee

Note : ce plan decrit le pilote v0/v1. Le pivot metier cible v2
`scope_level / signal_category` est documente dans
[`docs/assemblee_contextualization_contract_v2.md`](assemblee_contextualization_contract_v2.md).

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

## Providers

- Provider mock : conserve pour les tests et les runs sans API.
- Provider Mistral : premier provider reel de test.

Mistral est branche comme provider reel initial, sans devenir un choix definitif pour tout le projet.

Variables attendues pour un appel reel :

- `MISTRAL_API_KEY`
- `MISTRAL_MODEL`

Si `MISTRAL_MODEL` est absent, le provider utilise `mistral-medium-latest`.

Le projet peut lire ces variables depuis un fichier `.env` local non versionne.
Le fichier `.env.example` sert de modele sans secret.

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

## Politique de fallback

En cas de cle absente, d'erreur d'appel, de JSON non parseable ou de sortie non conforme :

- `decision = ambiguous`
- `needs_human_review = true`
- `confidence = low`
- `rationale` explique l'echec
- `limits` rappelle l'absence de recherche web

Ce fallback reste une sortie sure, pas une analyse reelle.

## Livrables attendus

- contrats d'entree et de sortie ;
- context builder minimal ;
- interface provider-agnostic ;
- provider mock stable ;
- provider Mistral de test ;
- reviewer minimal ;
- tests unitaires du squelette.

## Remis a plus tard

- choix definitif du provider LLM ;
- prompt final stabilise ;
- batch complet sur corpus local ;
- reinjection dans la timeline ;
- scoring complexe ;
- recherche web optionnelle ;
- interface de validation humaine.
