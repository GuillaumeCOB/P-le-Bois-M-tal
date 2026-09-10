# Pôle BOIS/METAL — Outil de gestion de projets

Outil interne inspiré de Monday.com : projets, sous-tâches, groupes par statut,
assignation de collaborateurs, budget, échéances, vues Calendrier et Gantt.

Hébergé sur **Streamlit Community Cloud** (gratuit, accessible de partout via
un lien web) avec les données stockées sur **Supabase** (base de données
gratuite, pour que rien ne soit perdu quand l'appli redémarre).

Il y a 3 étapes : créer un compte GitHub (héberge le code), créer un compte
Supabase (héberge les données), puis déployer sur Streamlit Community Cloud.
Compte 20-30 minutes la première fois, à ne faire qu'une seule fois.

## Étape 1 — Mettre le code sur GitHub

1. Créer un compte gratuit sur https://github.com si vous n'en avez pas.
2. Créer un nouveau dépôt (repository), par exemple `pole-bois-metal`, en
   privé si vous préférez que le code ne soit pas public.
3. Mettre tous les fichiers de ce dossier dans ce dépôt (via l'interface web
   GitHub — "Add file" > "Upload files" — ou via `git` si vous êtes à l'aise
   avec).

   **Important** : ne mettez jamais votre fichier `.streamlit/secrets.toml`
   (s'il existe) sur GitHub — il est volontairement exclu par le
   `.gitignore` fourni.

## Étape 2 — Créer la base de données Supabase

1. Créer un compte gratuit sur https://supabase.com et un nouveau projet
   (choisir une région proche, ex. Europe).
2. Dans le menu de gauche, aller dans **SQL Editor**, coller et exécuter :

   ```sql
   create table app_data (
     id integer primary key,
     data jsonb not null,
     updated_at timestamptz default now()
   );
   ```

3. Aller dans **Project Settings > API**. Noter deux valeurs :
   - **Project URL** (ex. `https://xxxxx.supabase.co`)
   - **service_role key** (une longue clé secrète — pas la clé "anon" !)

   ⚠️ La `service_role key` donne un accès complet à la base : elle ne doit
   jamais être partagée ni publiée nulle part (elle restera uniquement dans
   les secrets Streamlit, jamais visible des utilisateurs de l'appli).

## Étape 3 — Déployer sur Streamlit Community Cloud

1. Aller sur https://share.streamlit.io et se connecter avec le compte
   GitHub créé à l'étape 1.
2. Cliquer **"New app"**, choisir votre dépôt `pole-bois-metal`, et indiquer
   `app.py` comme fichier principal.
3. Avant de déployer (ou juste après), aller dans **"Advanced settings" >
   "Secrets"** et coller :

   ```
   SUPABASE_URL = "https://xxxxx.supabase.co"
   SUPABASE_KEY = "votre_service_role_key"
   ```

4. Cliquer **"Deploy"**. Après une minute ou deux, votre appli est en ligne à
   une adresse du type `https://pole-bois-metal.streamlit.app`.
5. Partager ce lien avec toute l'équipe — chacun peut l'ouvrir depuis
   n'importe quel navigateur, ordinateur ou téléphone, aucune installation
   nécessaire côté utilisateurs.

## Fonctionnement à plusieurs

- Toutes les personnes qui ouvrent le lien travaillent sur **les mêmes
  données**, stockées dans Supabase — pas de fichier à synchroniser, pas de
  délai.
- Les modifications sur des projets différents ne s'écrasent jamais entre
  elles. Si deux personnes modifient le **même** projet à quelques secondes
  d'intervalle, la dernière sauvegarde l'emporte (cas rare pour une équipe de
  3-4 personnes).
- Utilisez le bouton **"🔄 Rafraîchir les données"** dans la barre latérale
  pour voir immédiatement les changements faits par un collègue.

## Modifier l'application plus tard

Pour changer une fonctionnalité : modifiez les fichiers dans votre dépôt
GitHub (directement sur github.com ou en local avec `git`), Streamlit Cloud
redéploie automatiquement l'appli à chaque modification du dépôt.

## Test en local (optionnel, pour les développeurs)

```
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# éditer .streamlit/secrets.toml avec vos vraies valeurs Supabase
streamlit run app.py
```

## Utilisation de l'application

- **📋 Tableau** : vos projets, regroupés automatiquement par statut. Changer
  le statut d'un projet dans son formulaire d'édition le déplace
  automatiquement dans le bon groupe.
- **➕ Nouveau projet** : créer un projet avec assignation, budget, temps
  estimé et échéance.
- **📅 Calendrier** : vue mensuelle des échéances.
- **📊 Gantt** : vue échéancier de tous les projets ayant une date
  d'échéance.
- Barre latérale : gérer la liste des collaborateurs et des statuts/groupes
  (ajout, suppression).
