# Mise en place d'une nouvelle saison

Protocole détaillé (penser à le mettre à jour) - Loïc Simon, avril 2022

## Création du serveur

- Sur Discord, y créer un serveur vierge privé (le + tout en bas de la liste des serveurs)
- Y ajouter le bot en accédant à l'URL suivante : https://discord.com/oauth2/authorize?client_id=693899568156377181&permissions=8&scope=bot
- On peut aussi inviter tous les MJs, mais **NE PAS CRÉER DE SALONS OU RÔLES** !
- Récupérer l'ID du serveur (18 caractères) depuis les paramètres du serveur > Widget > Setup du bot

## Setup du bot

Pour la suite, on suppose que le bot tourne sur la Griway : sinon, adaptez, vous devriez savoir faire.

- Se connecter à la Griway et `sudo su lgrez`
- Dans `/home/lgrez`, copier le dossier de la dernière saison (`cp -r P22 H23` par ex.)
- Dans le nouveau dossier, modifier le fichier `.env` pour mettre à jour la variable `LGREZ_SERVER_ID`
  avec l'ID du serveur récupéré précédemment
- Sudo-modifier le fichier `/etc/supervisor/conf.d/lgrez.conf` avec la nouvelle saison.
  **ATTENTION 4 EMPLACEMENTS À CHANGER !**
- Appliquer la nouvelle config : `sudo supervisorctl reload`

Le bot devrait alors changer de serveur et devrait alors poster un message dans le nouveau serveur.
(si non, investiguer)

- Tant qu'on est là, modifier le fichier `start_bot.py` avec notamment à la toute fin la date de début de saison
  et la chambre MJ (peut être fait ultérieurement)
- Mettre à jour le bot, le cas échéant : `../env/bin/pip install --upgrade lg-rez`

## Setup de la BDD

- Sur la Griway toujours, aller dans le dossier de l'ancienne saison et backup la DB actuelle
  (pas obligé, mais fortement conseillé) : `pg_dump lgrez > backup.sql`
- Stop le bot : `sudo supervisorctl stop lgrez`
- Vider les tables de saison, et celles qui seront remplies plus tard par `/fillroles` :
  ```
  psql -d lgrez -c 'TRUNCATE joueurs, bouderies, boudoirs, taches, camps, baseactions, _baseactions_roles, ciblages, utilisations, actions RESTART IDENTITY CASCADE;'
  ```

## Setup du serveur

- Tu sais lire non ? Le bot il a dit de faire `/setup`, ben voilà
- Clean les 2-3 salons éventuellement restant et vérifier rapidement que tout à l'air OK (`/ping`)
- Faire un `/panik` et vérifier que le bot reboot bien en quelques secondes, et qu'il est content
- Personnaliser le nom et l'avatar du serveur
- Le serveur est prêt ! Mais attention c'est pas fini

## Setup du Drive

- Créer un dossier pour la dernière saison, si les flemmards de MJ passé l'ont pas déjà fait
- Créer une copie (Clic doit > Créer une copie) des QUATRE sheets à la racine du Drive, et déplacer LES COPIES dans
  le dossier de l'ancienne saison pour archive. **NE PAS DÉPLACER LES ORIGINAUX**, c'est eux auquel le bot accèdera !
- Ouvrir le [Tableau de bord](), cliquer sur `Extensions > Macros > Clean backup feuilles`
- Nettoyer la feuille Journée en cours en **AFFICHANT LES COLONNES A-K** puis en effaçant (suppr) toutes les lignes
  joueurs SUR LES COLONNES A-S : attention, **ne PAS effacer les colonnes T et U** !
  (la colonne V par contre pas de problème)
- Il restera quelques trucs à nettoyer (jor les premières feuilles), vous êtes grands
- Ouvrir le fichier [Données brutes]() et supprimer les lignes des quatre premières feuilles (celles en `_brut`,
  **PAS** les autres), **SAUF la première ligne** de chaque

## Invitation des joueurs et lancement du jeu

- Une fois tout validé dans [Rôles et actions](), appeler `/fillroles`
- Mettre les (autres) messages de base dans tous les salons où il en faut
- Si ça n'a pas été fait précédemment, modifier la date de début de saison et la chambre MJ dans start_bot.py
- Les joueurs peuvent maintenant être invités !
- À la fin de la période d'inscription, **RÉVOQUER TOUTES LES INVITATIONS**
- Le jour du lancement après 10h, appeler `/cparti` et **BIEN LIRE TOUTES LES INSTRUCTIONS** pitié
- Bon jeu !

## À la fin de la saison

- Féliciter le camp nécro pour sa victoire
- Appeler `/cfini` et **BIEN LIRE TOUTES LES INSTRUCTIONS** pitié
- Bon repos !
