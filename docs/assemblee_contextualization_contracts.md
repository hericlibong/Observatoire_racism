# Contrats contextualisation Assemblee

## Source metier principale

La source metier principale est l'export enrichi des interventions.

Pour le pilote :

- `data/interim/assemblee/interventions_test.csv`

Cet export contient toutes les interventions et les champs `signal_*`.

## Distinctions metier

- Interventions enrichies : toutes les interventions parsees, avec les champs rule-based.
- Candidats rule-based : sous-ensemble derive avec `signal_candidate = true`.
- Revue agentique : sortie structuree du contextualisateur.
- Revue humaine : statut et note saisis ou valides par une personne.

`signals_review_pilot.csv` peut aider la revue humaine, mais ne doit pas devenir la source principale de la brique agentique.

## Contrat d'entree

Payload minimal :

```json
{
  "candidate_id": "CRSANR5L17S2026O1N191_4053224",
  "source": {
    "source_file": "CRSANR5L17S2026O1N191.xml",
    "seance_id": "CRSANR5L17S2026O1N191",
    "intervention_id": "CRSANR5L17S2026O1N191_4053224"
  },
  "target": {
    "ordre": 33,
    "orateur_nom": "Mme Naima Moutchou",
    "point_titre": "Presentation",
    "sous_point_titre": "",
    "texte": "Texte complet du paragraphe cible."
  },
  "rule_based_signal": {
    "signal_candidate": true,
    "signal_family": "devalorisation",
    "signal_trigger": "irresponsable",
    "signal_intensity": 2
  },
  "local_context": {
    "previous": [],
    "next": []
  }
}
```

## Contrat de sortie

JSON strict minimal :

```json
{
  "candidate_id": "CRSANR5L17S2026O1N191_4053224",
  "decision": "ambiguous",
  "needs_human_review": true,
  "confidence": "medium",
  "rationale": "Le contexte local ne permet pas de trancher clairement.",
  "evidence_span": "extrait court utilise pour la decision",
  "limits": [
    "Analyse limitee au contexte local.",
    "Aucune recherche web effectuee."
  ],
  "model_provider": "mock",
  "model_name": "mock-contextual-reviewer-v0"
}
```

## Enums autorisees

`decision` :

- `validated_signal`
- `false_positive`
- `ambiguous`

`confidence` :

- `low`
- `medium`
- `high`

## Regles decision / revue humaine

- `ambiguous` implique `needs_human_review = true`.
- `validated_signal` implique `needs_human_review = true` en v0.
- `false_positive` peut avoir `needs_human_review = false` si le cas est clair.
- `false_positive` peut avoir `needs_human_review = true` si le cas reste sensible.
- `needs_human_review` reste un booleen separe de `decision`.

## Contraintes

- Pas de recherche web par defaut.
- Pas de verdict moral automatique.
- Pas de provider LLM impose.
- Pas de modification du parsing XML.
- Pas de modification de la timeline D3 en v0.

## Provider Mistral

Mistral est le premier provider reel branche pour tester le workflow.

Variables d'environnement :

- `MISTRAL_API_KEY` : cle API Mistral.
- `MISTRAL_MODEL` : modele a utiliser.

Valeur par defaut si `MISTRAL_MODEL` est absent :

- `mistral-medium-latest`

Commande de run pilote :

```bash
python -m src.assemblee_contextualization.run_pilot --provider mistral
```

Sortie :

- `data/interim/assemblee/contextual_reviews_pilot.jsonl`

Politique de fallback :

- cle API absente ;
- erreur d'appel ;
- sortie non parseable ;
- sortie non conforme au contrat.

Dans ces cas, la sortie reste conforme :

```json
{
  "decision": "ambiguous",
  "needs_human_review": true,
  "confidence": "low"
}
```

Le champ `rationale` doit expliquer l'echec.
