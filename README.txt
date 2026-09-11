Outil interne de gestion de projets - Builders / Verticalsea
===========================================================

STRUCTURE DU PROJET
-------------------
Projet
  -> Sous-projet / phase
       -> Tache

Le projet porte :
- Numero de projet
- Nom
- Client
- Structure : Bois / Metal ou Beton
- Budget total calcule automatiquement = somme des budgets des sous-projets
- Heures totales calculees automatiquement = somme des heures des sous-projets

Chaque sous-projet / phase porte :
- Phase
- Type
- Collaborateurs
- Statut
- Echeance
- Budget
- Heures

Chaque tache porte :
- Nom
- Collaborateurs
- Statut
- Echeance
- Budget
- Heures

FACTURATION
-----------
Une case "A facturer" est disponible sur les 3 niveaux.
Le clic enregistre l'heure exacte en fuseau Europe/Paris et le montant au moment du clic.
Le nouvel onglet "A facturer" regroupe ensuite les elements par mois de facturation.

Pour eviter les doubles comptages :
- si un projet complet est coche, ses sous-projets et taches sont retires de la facturation individuelle ;
- si un sous-projet est coche, ses taches sont retirees de la facturation individuelle.

MIGRATION DES DONNEES EXISTANTES
--------------------------------
La migration est automatique au premier chargement :
- chaque ancien projet devient un projet de niveau 1 ;
- ses anciennes informations operationnelles deviennent un premier sous-projet ;
- ses anciennes sous-taches deviennent des taches ;
- les anciens projets sont classes par defaut en "Bois / Metal" ;
- le champ Client est initialise vide.

Il est recommande de conserver une sauvegarde des donnees Supabase avant le premier deploiement de cette version.

DEPLOIEMENT
-----------
Conserver les fichiers/dossiers :
- .gitignore
- .devcontainer/
- .streamlit/
- storage.py
- requirements.txt
- assets/
- ui/
- views/

Ne jamais publier .streamlit/secrets.toml dans GitHub.
Le .gitignore fourni l'exclut deja.

Lancement local :
streamlit run app.py
