# Checklist

- [x] Creer et figer un XML test unique de reference
- [x] Fixer `CRSANR5L17S2026O1N191.xml` comme fichier pilote unique
- [x] Noter son chemin exact dans le projet
- [x] Identifier les balises utiles pour la seance, les points et les interventions
- [x] Lister les champs XML vraiment fiables
- [x] Fixer le schema minimal de la table `interventions`
- [x] Definir la structure de `data/interim/assemblee/source_manifest.json`
- [x] Limiter le manifest a l'inventaire source : nom, chemin, taille, date locale si disponible
- [x] Definir la regle : 1 ligne = 1 paragraphe / intervention
- [x] Definir la regle de calcul de `ordre` dans la seance
- [x] Extraire `texte`, `nb_mots` et `nb_caracteres`
- [x] Produire un premier export tabulaire de controle
- [x] Verifier manuellement quelques interventions dans l'export
- [x] Produire un JSON minimal pour D3 a partir du meme XML test
- [x] Definir l'encodage couleur comme intensite de signal candidat
- [ ] Monter une premiere timeline intra-seance en D3
- [ ] Verifier que la timeline suit bien l'ordre reel de la seance
- [ ] Noter les champs absents, ambigus ou non fiables pour la suite
