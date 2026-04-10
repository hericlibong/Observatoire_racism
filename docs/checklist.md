# Checklist

- [ ] Creer et figer un XML test unique de reference
- [ ] Fixer `CRSANR5L17S2026O1N191.xml` comme fichier pilote unique
- [ ] Noter son chemin exact dans le projet
- [ ] Identifier les balises utiles pour la seance, les points et les interventions
- [ ] Lister les champs XML vraiment fiables
- [ ] Fixer le schema minimal de la table `interventions`
- [ ] Definir la structure de `data/interim/assemblee/source_manifest.json`
- [ ] Limiter le manifest a l'inventaire source : nom, chemin, taille, date locale si disponible
- [ ] Definir la regle : 1 ligne = 1 paragraphe / intervention
- [ ] Definir la regle de calcul de `ordre` dans la seance
- [ ] Extraire `texte`, `nb_mots` et `nb_caracteres`
- [ ] Produire un premier export tabulaire de controle
- [ ] Verifier manuellement quelques interventions dans l'export
- [ ] Produire un JSON minimal pour D3 a partir du meme XML test
- [ ] Definir l'encodage couleur comme intensite de signal candidat
- [ ] Monter une premiere timeline intra-seance en D3
- [ ] Verifier que la timeline suit bien l'ordre reel de la seance
- [ ] Noter les champs absents, ambigus ou non fiables pour la suite
