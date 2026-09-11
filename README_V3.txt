VERSION HIERARCHIE V3

Principales evolutions :
- Tableau principal groupe par statut de projet.
- Statut porte uniquement par le projet dans l'interface.
- Structure Bois / Metal ou Beton affichee sur la ligne projet.
- Sous-projet : Phase et Type fusionnes en un seul champ Type.
- Taches sans statut propre dans l'interface.
- Alignement vertical renforce sur Projet / Sous-projet / Tache.
- Lorsqu'un element est coche A facturer, sa ligne disparait du Tableau et reste disponible dans l'onglet A facturer.
- Migration automatique du modele de donnees vers la version 3.

Fichiers principalement modifies :
- storage.py
- config.py
- ui/components.py
- ui/styles.py
- views/tableau.py
- views/nouveau_projet.py
- views/a_facturer.py
- views/calendrier.py
- views/gantt.py
- views/parametres.py
