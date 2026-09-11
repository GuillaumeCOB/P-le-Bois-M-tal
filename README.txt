REORGANISATION DU PROJET
========================

1. Conserver à la racine vos fichiers existants :
   - storage.py
   - requirements.txt
   - .streamlit/secrets.toml uniquement en local si vous en utilisez un

2. Remplacer l'ancien app.py par le nouvel app.py.

3. Ajouter à la racine :
   - config.py
   - data_service.py

4. Ajouter les dossiers :
   - ui/
   - views/

5. Conserver le dossier assets/ et son logo.

Structure finale :

projet/
├── app.py
├── config.py
├── data_service.py
├── storage.py                 <- votre fichier actuel, inchangé
├── requirements.txt           <- votre fichier actuel, inchangé
├── assets/
│   └── logo_builders_verticalsea.png
├── ui/
│   ├── __init__.py
│   ├── components.py
│   ├── header.py
│   └── styles.py
└── views/
    ├── __init__.py
    ├── tableau.py
    ├── nouveau_projet.py
    ├── calendrier.py
    ├── gantt.py
    └── parametres.py

Aucune migration Supabase n'est nécessaire.
La réorganisation ne change pas la structure des données.
