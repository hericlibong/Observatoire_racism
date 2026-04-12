# Contrat contextualisation Assemblee v2

## Objet

Ce contrat v2 remplace le schema metier cible `validated_signal / false_positive / ambiguous`.
Il ne remplace pas encore le pipeline pilote.

Le contextualisateur ne produit pas de verdict moral. Il qualifie :

- un niveau de perimetre : `scope_level` ;
- un type de signal a revoir : `signal_category` ;
- un marqueur de fallback technique : `is_fallback` ;
- un besoin de revue humaine : `needs_human_review`.

Le coeur de l'observatoire reste strictement limite aux signaux lies a la haine,
au racisme, a la xenophobie, a la discrimination, ou au ciblage problematique
de groupes lies notamment a l'origine, la nationalite, l'ethnicite reelle ou
supposee, la religion, ou a d'autres categories pertinentes du meme perimetre
discriminatoire.

## Forme de sortie cible

```json
{
  "candidate_id": "CRSANR5L17S2026O1N191_4053224",
  "scope_level": "adjacent",
  "signal_category": "ambiguous",
  "is_fallback": false,
  "needs_human_review": true,
  "confidence": "low",
  "rationale": "Le contexte local ne permet pas de qualifier un signal core.",
  "evidence_span": "extrait court utilise pour la qualification",
  "limits": [
    "Analyse limitee au contexte local.",
    "Aucune recherche web effectuee."
  ],
  "model_provider": "mock",
  "model_name": "mock-contextual-reviewer-v0"
}
```

## Enums definitives

`scope_level` :

- `core`
- `adjacent`
- `hors_perimetre`

`signal_category` :

- `problematic_group_targeting`
- `stereotype_essentialization`
- `devaluation_dehumanization`
- `exclusion_discrimination`
- `hostility_threat`
- `ambiguous`
- `no_signal`

`confidence` reste :

- `low`
- `medium`
- `high`

## Definitions strictes

`core` designe uniquement un cas relevant clairement du coeur de l'observatoire :
un groupe du perimetre est cible explicitement ou de facon fortement inferable,
et le passage porte un signal substantiel relevant de la haine, du racisme, de
la xenophobie, de la discrimination ou d'un ciblage discriminatoire comparable.

`core` n'inclut pas les tensions politiques ordinaires, polemiques
parlementaires, critiques institutionnelles, attaques partisanes, critiques de
personnes publiques, groupes professionnels, groupes comportementaux ordinaires
ou hostilite generique sans lien clair avec le perimetre haine / discrimination /
xenophobie / racisme.

`adjacent` designe un cas frontiere. Il est autorise seulement si un ancrage
plausible existe avec le perimetre de l'observatoire, mais que le contexte local
ne suffit pas a qualifier `core` proprement : reference indirecte, citation ou
reprise a clarifier, cible collective implicite, ou mecanisme discriminatoire
possible mais non stabilise.

`adjacent` ne doit pas absorber les discours simplement durs, securitaires,
moralisateurs, conflictuels ou partisans sans ancrage suffisant dans le
perimetre. En l'absence de cet ancrage, utiliser `hors_perimetre`.

`hors_perimetre` designe un passage sans ancrage suffisant dans le perimetre de
l'observatoire : tension politique ordinaire, attaque partisane, critique d'une
institution, critique d'une strategie parlementaire, critique d'une personne
publique, ou discours dur sans ciblage problematique d'un groupe relevant du
perimetre.

## Categories de signal

`problematic_group_targeting` : ciblage explicite ou fortement inferable d'un
groupe relevant du perimetre discriminatoire, quand le probleme principal est le
ciblage du groupe lui-meme plutot qu'un mecanisme plus precis ci-dessous.

`stereotype_essentialization` : attribution generalisante ou essentialisante a
un groupe du perimetre, y compris naturalisation d'un comportement, d'une menace
ou d'une incompatibilite supposee.

`devaluation_dehumanization` : devalorisation, inferiorisation,
deshumanisation ou disqualification globale d'un groupe du perimetre.

`exclusion_discrimination` : appel, justification ou mise en scene d'un
traitement differencie, d'une exclusion, d'une restriction de droits ou d'un
tri visant un groupe du perimetre.

`hostility_threat` : hostilite, menace, legitimation de violence ou
stigmatisation agressive visant un groupe du perimetre.

`ambiguous` : le type de signal ne peut pas etre stabilise a partir du contexte
local. Ce n'est pas un signal positif. Avec `hors_perimetre`, cette valeur est
reservee au fallback technique explicite `is_fallback = true`.

`no_signal` : aucun signal du perimetre n'est qualifie. Cette valeur est
reservee a `hors_perimetre`.

## Matrice des combinaisons

| scope_level | problematic_group_targeting | stereotype_essentialization | devaluation_dehumanization | exclusion_discrimination | hostility_threat | ambiguous | no_signal |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `core` | valide | valide | valide | valide | valide | invalide | invalide |
| `adjacent` | valide | valide | valide | valide | valide | valide | invalide |
| `hors_perimetre` | invalide | invalide | invalide | invalide | invalide | valide seulement si `is_fallback = true` | valide |

Regles complementaires :

- `no_signal` est autorise uniquement avec `hors_perimetre`.
- `ambiguous` est autorise avec `adjacent` pour un cas frontiere non stabilise.
- `ambiguous` est autorise avec `hors_perimetre` uniquement pour un fallback
  technique explicite avec `is_fallback = true` ; ce n'est jamais une conclusion
  substantielle de hors-perimetre.
- `ambiguous` est invalide avec `core` : si le cas est `core`, une categorie
  substantielle doit etre choisie.
- Toute categorie substantielle est invalide avec `hors_perimetre`.

## is_fallback

`is_fallback` est un marqueur technique, pas une categorie metier.

`is_fallback = true` est autorise uniquement avec la combinaison exacte :

- `scope_level = hors_perimetre` ;
- `signal_category = ambiguous` ;
- `needs_human_review = true` ;
- `confidence = low`.

Toutes les sorties substantives normales doivent avoir `is_fallback = false`,
y compris :

- tout `core` ;
- tout `adjacent`, y compris `adjacent / ambiguous` ;
- tout vrai `hors_perimetre / no_signal`.

`hors_perimetre / ambiguous` avec `is_fallback = false` est invalide.
`is_fallback = true` est invalide avec `core`, `adjacent` et
`hors_perimetre / no_signal`.

## needs_human_review

`needs_human_review = true` est systematique pour :

- tout `core` ;
- tout `adjacent` ;
- tout `signal_category = ambiguous` ;
- tout fallback technique avec `is_fallback = true` ;
- toute confiance `low` ou `medium` ;
- toute cible collective implicite ou incertaine ;
- toute citation, reprise, negation, ironie ou attribution de propos a un tiers
  qui rend la qualification dependante du contexte ;
- tout cas ou le groupe cible, le mecanisme discriminatoire ou le role de
  l'orateur n'est pas clair.

`needs_human_review = false` est autorise seulement si toutes les conditions
suivantes sont remplies :

- `scope_level = hors_perimetre` ;
- `signal_category = no_signal` ;
- `confidence = high` ;
- le rationale indique clairement l'absence d'ancrage dans le perimetre de
  l'observatoire.

`needs_human_review` reste un champ de routage. Il ne transforme jamais un
signal en verdict.

## Fallback

En cas de cle absente, d'erreur d'appel, de JSON non parseable, de sortie non
conforme ou de contexte local inexploitable, la sortie v2 sure est :

```json
{
  "scope_level": "hors_perimetre",
  "signal_category": "ambiguous",
  "is_fallback": true,
  "needs_human_review": true,
  "confidence": "low"
}
```

Le `rationale` doit expliquer le fallback. Les `limits` doivent rappeler au
minimum l'analyse limitee au contexte local et l'absence de recherche web.
Cette combinaison ne doit pas etre comptee comme un vrai cas hors perimetre :
elle represente uniquement l'echec controle de la qualification.

## Exemples limites

Exemples `core` :

- Un passage attribue une menace naturelle a un groupe defini par l'origine ou
  la religion. Justification : ciblage clair du perimetre et essentialisation.
- Un passage defend une restriction de droits visant explicitement une
  nationalite ou une origine. Justification : cible du perimetre et categorie
  `exclusion_discrimination`.
- Un passage devalorise globalement un groupe ethnique ou religieux suppose.
  Justification : cible du perimetre et categorie `devaluation_dehumanization`.

Exemples `adjacent` :

- Un passage parle d'une incompatibilite culturelle sans nommer le groupe, mais
  le contexte local suggere un lien possible avec l'origine ou la religion.
  Justification : ancrage plausible, mais cible et signal a stabiliser.
- Un passage cite un slogan discriminatoire pour le denoncer, avec un contexte
  local incomplet. Justification : signal du perimetre present, role de la
  citation a verifier.
- Un passage sur une mesure de securite vise indirectement une pratique
  religieuse sans cible explicite. Justification : lien possible au perimetre,
  mais qualification `core` insuffisamment etablie.

Exemples `hors_perimetre` :

- Une attaque contre le Gouvernement, un parti ou un groupe parlementaire.
  Justification : conflit politique ordinaire, pas de groupe du perimetre.
- Une critique d'une institution, d'une procedure ou d'une strategie
  parlementaire. Justification : critique institutionnelle sans ciblage
  discriminatoire.
- Une formule dure visant des fraudeurs, delinquants ou comportements sans lien
  avec une origine, nationalite, ethnicite, religion ou categorie comparable.
  Justification : groupe comportemental ordinaire, pas de signal du perimetre.
