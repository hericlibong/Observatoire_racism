# Taches Assemblee - signaux candidats

Note : cette checklist reste l'historique de la phase signaux et du pipeline
pilote. Le planning actif est desormais suivi dans
[`docs/assemblee_roadmap.md`](assemblee_roadmap.md).

## Phase A - enrichir le fichier pilote

- [x] Relire la structure actuelle de l'export pilote.
- [x] Identifier les champs deja disponibles pour chaque intervention.
- [x] Ajouter un champ de presence de signal candidat.
- [x] Ajouter un champ de type ou famille de signal candidat.
- [x] Ajouter un champ de justification courte du signal.
- [x] Ajouter un champ de niveau d'intensite visuelle pour D3.
- [x] Produire un export tabulaire pilote enrichi.
- [x] Produire un JSON D3 pilote enrichi.
- [x] Adapter la timeline D3 pour afficher les signaux candidats.
- [x] Verifier que l'affichage ne presente pas le signal comme un jugement.
- [x] Produire un tableau de revue humaine des signaux du fichier pilote.

## Phase B - stabiliser la methode

- [x] Lister les regles de detection utilisees.
- [x] Lister les champs conserves pour la suite.
- [x] Verifier un echantillon de passages signales.
- [x] Noter les faux positifs visibles.
- [ ] Noter les faux negatifs visibles.
- [x] Noter les cas ambigus.
- [ ] Ajuster les regles trop bruyantes.
- [x] Fixer le format minimal de sortie.
- [ ] Documenter les limites de la methode.
- [x] Produire un tableau comparatif signaux rule-based / contextualisation.

## Phase C - etendre au corpus local Assemblee

- [ ] Relire le manifest des sources locales.
- [ ] Selectionner un petit lot de XML Assemblee locaux.
- [ ] Appliquer l'extraction enrichie au lot selectionne.
- [ ] Produire un export tabulaire multi-fichiers.
- [ ] Produire un JSON D3 multi-fichiers simple.
- [ ] Verifier que chaque ligne garde sa reference source.
- [ ] Controler un echantillon de fichiers traites.
- [ ] Noter les erreurs de parsing ou de structure XML.
- [ ] Decider si la methode peut etre appliquee au corpus local complet.

## Phase D - automatiser la collecte

- [ ] Identifier la source de collecte Assemblee a utiliser.
- [ ] Definir le dossier de destination des fichiers collectes.
- [ ] Definir une regle de nommage stable.
- [ ] Ecrire une commande ou un script de collecte minimal.
- [ ] Ajouter un journal des fichiers recuperes.
- [ ] Eviter les doublons lors d'une nouvelle collecte.
- [ ] Tester la collecte sur un petit volume.
- [ ] Documenter la commande de collecte.

## Phase E - articuler signaux et contextualisation

- [ ] Relire les sorties contextualisees du fichier pilote.
- [ ] Verifier la coherence entre signaux rule-based et decisions contextualisees.
- [ ] Identifier quelques cas representatifs par famille de signal.
- [ ] Identifier les faux positifs et cas ambigus utiles a la stabilisation.
- [ ] Decider quels champs contextualises doivent etre ajoutes au JSON D3.
- [ ] Adapter la timeline D3 avec les champs contextualises retenus.
- [ ] Verifier que la visualisation reste lisible.
- [ ] Verifier que la visualisation ne presente pas la contextualisation comme un verdict.

## Remis a plus tard

- [ ] Entrainer un modele de classification.
- [ ] Produire un score definitif.
- [ ] Qualifier automatiquement un passage comme raciste, discriminatoire ou haineux.
- [ ] Construire un tableau de bord consolide.
- [ ] Mettre en place une base de donnees.
- [ ] Etendre la methode hors corpus Assemblee.
