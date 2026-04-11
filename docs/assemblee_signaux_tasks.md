# Taches Assemblee - signaux candidats

## Phase A - enrichir le fichier pilote

- [ ] Relire la structure actuelle de l'export pilote.
- [ ] Identifier les champs deja disponibles pour chaque intervention.
- [ ] Ajouter un champ de presence de signal candidat.
- [ ] Ajouter un champ de type ou famille de signal candidat.
- [ ] Ajouter un champ de justification courte du signal.
- [ ] Ajouter un champ de niveau d'intensite visuelle pour D3.
- [ ] Produire un export tabulaire pilote enrichi.
- [ ] Produire un JSON D3 pilote enrichi.
- [ ] Adapter la timeline D3 pour afficher les signaux candidats.
- [ ] Verifier que l'affichage ne presente pas le signal comme un jugement.

## Phase B - stabiliser la methode

- [ ] Lister les regles de detection utilisees.
- [ ] Lister les champs conserves pour la suite.
- [ ] Verifier un echantillon de passages signales.
- [ ] Noter les faux positifs visibles.
- [ ] Noter les faux negatifs visibles.
- [ ] Noter les cas ambigus.
- [ ] Ajuster les regles trop bruyantes.
- [ ] Fixer le format minimal de sortie.
- [ ] Documenter les limites de la methode.

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

## Phase E - ajouter la couche contextuelle

- [ ] Ajouter les informations de seance utiles a la relecture.
- [ ] Ajouter les informations de point de debat utiles a la relecture.
- [ ] Ajouter les references source disponibles.
- [ ] Ajouter le contexte avant et apres intervention si disponible.
- [ ] Adapter le JSON D3 pour porter ces champs.
- [ ] Adapter la timeline D3 pour afficher le contexte de lecture.
- [ ] Verifier que le contexte reste lisible.
- [ ] Verifier que la timeline ne transforme pas le signal en verdict.

## Remis a plus tard

- [ ] Entrainer un modele de classification.
- [ ] Produire un score definitif.
- [ ] Qualifier automatiquement un passage comme raciste, discriminatoire ou haineux.
- [ ] Construire un tableau de bord consolide.
- [ ] Mettre en place une base de donnees.
- [ ] Etendre la methode hors corpus Assemblee.
