import os
import time             # Accès à date/heure actuelle
import traceback        # Récupération des messages d'erreur Python, pour les afficher plutôt que planter le site
import random           # Génération de nombres aléatoires, choix aléatoires...
import string           # Génération de texte aléatoire
import difflib          # Contient SequenceMatcher : déterminer les chaînes de caractères les plus ressemblantes
import requests         # Requêtes HTML (GET, POST...)
import json             # JSON -> dictionnaire et inversement, pour échange données
import unidecode        # Comparaison de chaînes en enlèvant les accents

from dotenv import load_dotenv
import sqlalchemy.ext
from sqlalchemy.exc import *                            # Exceptions générales SQLAlchemy
from sqlalchemy.orm.exc import *                        # Exceptions requêtes SQLAlchemy

import Discord.blocs.gsheets as gsheets         # Connection à Google Sheets (maison)
import Discord.blocs.webhook as webhook         # Envoi de webhook Discord
from Discord.blocs import bdd_tools             # Outils BDD
from __init__ import db, Tables, Joueurs        # Récupération BDD


# CONSTANTES

load_dotenv()
GLOBAL_PASSWORD = os.getenv("GLOBAL_PASSWORD")
assert GLOBAL_PASSWORD, "core.py : GLOBAL_PASSWORD introuvable"

ALWAYSDATA_API_KEY = os.getenv("ALWAYSDATA_API_KEY")
assert ALWAYSDATA_API_KEY, "core.py : ALWAYSDATA_API_KEY introuvable"

jobs = ["open_cond", "remind_cond", "close_cond",
        "open_maire", "remind_maire", "close_maire",
        "open_loups", "remind_loups", "close_loups",
        "open_action", "remind_action", "close_action",
        ]


### UTILITAIRES

def strhtml(r):
    r"""Échappe &, <, > et \n en leur code HTML correspondant"""
    return r.replace('&','&esp;').replace('<','&lt;').replace('>','&gt;').replace('\n', '<br/>')

def html_escape(r):
    r"""Échappe &, < et > en leur code HTML correspondant (comme strhtml, mais conserve les \n)"""
    return str(r).replace('&','&esp;').replace('<','&lt;').replace('>','&gt;')

def infos_tb(quiet=False):
    """Renvoie traceback.format_exc() tel quel (si <quiet>) ou en mode HTML"""
    tb = traceback.format_exc()
    if quiet:
        return tb
    else:
        return f"<br/><div> AN EXCEPTION HAS BEEN RAISED! <br/><pre>{html_escape(tb)}</pre></div>"

def getjobs():
    """Récupère la liste des tâches planifiées sur l'API alwaysdata"""
    rep = requests.get('https://api.alwaysdata.com/v1/job/', auth=(ALWAYSDATA_API_KEY, ''))
    if rep:
        try:
            lst = rep.json()
        except:
            lst = []
    else:
        raise ValueError(f"Request Error (HTTP code {rep.status_code})")
    return lst


### SYNCHRONISATION DU TABLEAU DE BORD

def sync_TDB(d):
    """Fonction appellée par le script du Tableau de bord, à la synchronisation

    <d> : pseudo-dictionnaire des arguments passés en GET (juste pour pwd, normalement)
    """
    r = ""
    try:
        verbose = ('v' in d)        # Messages d'erreur/... détaillés
        silent = ('s' in d)         # Ne prévient pas les joueurs des modifications
        if verbose:
            r += "sync_TDB:"

        if ("pwd" in d) and (d["pwd"] == GLOBAL_PASSWORD):      # Vérification mot de passe

            ### GÉNÉRALITÉS

            cols = [col for col in bdd_tools.get_cols(Joueurs) if not col.startswith('_')]    # On élimine les colonnes locales
            cols_SQL_types = bdd_tools.get_SQL_types(Joueurs)
            cols_SQL_nullable = bdd_tools.get_SQL_nullable(Joueurs)

            ### RÉCUPÉRATION INFOS GSHEET

            if "sheet_id" in d:
                SHEET_ID = d["sheet_id"]
            else:
                raise ValueError("""Argument "sheet_id" manquant dans GET""")

            workbook = gsheets.connect(SHEET_ID)    # Tableau de bord
            sheet = workbook.worksheet("Journée en cours")
            values = sheet.get_all_values()         # Liste de liste des valeurs des cellules
            (NL, NC) = (len(values), len(values[0]))

            if verbose:
                r += f"<{NL}L/{NC}C>\n"

            head = values[2]            # Ligne d'en-têtes (noms des colonnes) = 3e ligne du TDB
            TDB_index = {col: head.index(col) for col in cols}    # Dictionnaire des indices des colonnes GSheet pour chaque colonne de la table
            TDB_tampon_index = {col: head.index(f"tampon_{col}") for col in cols if col != 'discord_id'}    # Idem pour la partie « tampon »

            # CONVERSION INFOS GSHEET EN UTILISATEURS

            joueurs_TDB = []            # Liste des joueurs tels qu'actuellement dans le TDB
            ids_TDB = []                # discord_ids des différents joueurs du TDB
            rows_TDB = {}               # Indices des lignes ou sont les différents joueurs du TDB

            for l in range(NL):
                L = values[l]           # On parcourt les lignes du TDB
                id_cell = L[TDB_index["discord_id"]]
                if id_cell.isdigit():        # Si la cellule contient bien un ID (que des chiffres, et pas vide)
                    id = int(id_cell)
                    joueur_TDB = {col: bdd_tools.transtype(L[TDB_index[col]], col, cols_SQL_types[col], cols_SQL_nullable[col]) for col in cols}
                        # Dictionnaire correspondant à l'utilisateur
                    joueurs_TDB.append(joueur_TDB)
                    ids_TDB.append(id)
                    rows_TDB[id] = l

            ### RÉCUPÉRATION UTILISATEURS CACHE

            joueurs_cache = Joueurs.query.all()     # Liste des joueurs tels qu'actuellement en cache
            ids_cache = [joueur_cache.discord_id for joueur_cache in joueurs_cache]

            ### COMPARAISON

            Modifs = []         # Modifs à porter au TDB : tuple (id - colonne (nom) - valeur)
            Modified_ids = []

            for joueur_cache in joueurs_cache.copy():                   ## Joueurs dans le cache supprimés du TDB
                if joueur_cache.discord_id not in ids_TDB:
                    joueurs_cache.remove(joueur_cache)
                    db.session.delete(joueur_cache)
                    if verbose:
                        r += f"\nJoueur dans le cache hors TDB : {joueur_cache}"

            for joueur_TDB in joueurs_TDB:                              ## Différences
                id = joueur_TDB["discord_id"]

                if id not in ids_cache:             # Si joueur dans le cache pas dans le TDB
                    raise ValueError(f"Joueur {joueur_TDB['nom']} hors BDD : vérifier processus d'inscription")

                joueur_cache = [joueur for joueur in joueurs_cache if joueur.discord_id == id][0]     # joueur correspondant dans le cache

                for col in cols:
                    if getattr(joueur_cache, col) != joueur_TDB[col]:   # Si <col> diffère entre TDB et cache
                        if verbose:
                            r += f"\n---- Colonne différant : {col} (TDB : {joueur_TDB[col]}, Joueurs : {getattr(joueur_cache, col)})"

                        bdd_tools.modif(joueur_cache, col, joueur_TDB[col])     # On modifie le cache (= BDD Joueurs)
                        Modifs.append( (id, col, joueur_TDB[col]) )   # On ajoute les modifs
                        if id not in Modified_ids:
                            Modified_ids.append(id)

            ### ENVOI WEBHOOK DISCORD

            if Modifs:
                dico = {id: {col: v for (idM, col, v) in Modifs if idM == id} for id in Modified_ids}
                message = f"!sync {silent} {json.dumps(dico)}"      # On transfère les infos sous forme de JSON (dictionnaire sérialisé)

                rep = webhook.send(message, "sync")
                if not rep:
                    raise Exception(f"L'envoi du webhook Discord a échoué : {rep} {rep.text}")

            ### APPLICATION DES MODIFICATIONS SUR LE TDB

            if Modifs:
                Modifs_lc = [(rows_TDB[id], TDB_tampon_index[col], v) for (id, col, v) in Modifs]
                    # On transforme les infos en coordonnées dans le TDB : ID -> ligne et col -> colonne,
                gsheets.update(sheet, Modifs_lc)

                if verbose:
                    r += "\n\n" + "\n".join([str(m) for m in Modifs])

            ### APPLICATION DES MODIFICATIONS SUR LES BDD cache

            db.session.commit()     # Modification de Joueurs

        else:
            raise ValueError("WRONG OR MISSING PASSWORD!")

    except Exception as e:
        db.session.rollback()
        if verbose:     # Affiche le "traceback" (infos d'erreur Python) en cas d'erreur (plutôt qu'un 501 Internal Server Error)
            return f"{strhtml(r)}<br/><br/><pre>{traceback.format_exc()}</pre>"
        else:
            return (400, f"{type(e).__name__}({str(e)})")
    else:
        return f"<pre>{r}</pre>"


### APPEL D'UNE TÂCHE PLANIFIÉE

def cron_call(d):
    """Fonction appellée par une tâche planifiée Alwaysdata (normalement obsolète)

    <d> : pseudo-dictionnaire des arguments passés en GET (juste pour pwd, normalement)
    """
    r = ""
    try:
        if ("pwd" in d) and (d["pwd"] == GLOBAL_PASSWORD):      # Vérification mot de passe
            if ("job" in d) and (d["job"] in jobs):             # jobs : défini en début de fichier, car utile dans admin
                job = d["job"]

                quoi, qui = job.split('_')      # "open_loups" -> "open", "loups"

                heure = d["heure"] if "heure" in d and d["heure"].isdigit() else ""

                rep = webhook.send(f"!{quoi} {qui} {heure}", "tp")      # Envoi Webhook Discord
                if not rep:
                    raise Exception(f"L'envoi du webhook Discord a échoué : {rep} {rep.text}")
            else:
                raise ValueError("""Bad usage: required argument "job" not in GET or incorrect""")
        else:
            raise ValueError("WRONG OR MISSING PASSWORD!")

    except Exception as e:
        return (400, f"{type(e).__name__}({str(e)})")

    else:
        return r


### OPTIONS DU PANNEAU D'ADMIN

exec(open("./Discord/blocs/admin_options.py").read())       # Comme si le code de admin_options était écrit ici (séparé pour plus de lisibilité)


### PANNEAU D'ADMIN

def manual(d):
    """Options d'administration automatiques (ajout,...) - pour tests/debug seulement !"""
    return admin(d, d)

def admin(d, p):
    """Fonction appellée par l'appel au panneau d'administration

    <d> : pseudo-dictionnaire des arguments passés en GET (juste pour pwd, normalement)
    <p> : pseudo-dictionnaire des arguments passés en POST (option du panneau d'admin et paramètres)
    """
    r = ""
    try:
        if ("pwd" in d) and (d["pwd"] == GLOBAL_PASSWORD):      # Vérification mot de passe
            r += f"""<h1><a href="admin?pwd={GLOBAL_PASSWORD}">Panneau d'administration LG Rez</a></h1><hr/>"""

            ### BASE DE DONNÉES

            if "viewtable" in p:
                r += viewtable(d, p)

            for k in p.keys():
                if k.startswith("viewtable-sort"):
                    [_, sort_col, sort_asc] = k.split(':')
                    r += viewtable(d, p, sort_col, sort_asc=="asc")

            if "additem" in p:
                r += additem(d, p)
                r += viewtable(d, p)

            if "delitem" in p:
                r += delitem(d, p)
                r += viewtable(d, p)

            if "editem" in p:
                r += editem(d, p)
                r += viewtable(d, p)

            # TÂCHES PLANIFIÉES

            if "viewcron" in p:
                r += viewcron(d, p)

            if "addcron" in p:
                r += addcron(d, p)
                r += viewcron(d, p)

            if "delcron" in p:
                r += delcron(d, p)
                r += viewcron(d, p)

            if "disablecron" in p:
                r += disablecron(d, p)
                r += viewcron(d, p)

            if "disablecron" in d:      # LORSQUE appelé depuis les statuts
                ids = d["id"].split(',')    # permet de modifier plusieurs ids d'un coup
                for id in ids:
                    r += disablecron(d, d, id)

            # AUTRES FONCTIONNALITÉS

            if "sendjob" in p:
                r += sendjob(d, p)

            if "viewlogs" in p:
                r += viewlogs(d, p)

            if "restart_site" in p:
                r += restart_site(d, p)

            # FONCTIONNALITÉS DEBUG

            if "testsheets" in d:
                workbook = gsheets.connect("1D5AWRmdGRWzzZU9S665U7jgx7U5LwvaxkD8lKQeLiFs")  # [DEV NextStep]
                sheet = workbook.worksheet("Journée en cours")
                values = sheet.get_all_values()     # Liste de liste des valeurs
                r += "<br/>TEST SHEETS.<br/>"
                r += "<p>values[8][8]:" + strhtml(values[8][8]) + "</p><br /><br />"

            if "oskour" in d:
                r += "OSKOUR<br/>"
                db.session.rollback()
                r += "OSKOUUUUR<br/>"

            ### STATUTS

            if ("statuts" in p) or (not p):   # si statuts demandés, ou si rien passé en POST
                r += show_statuts(d, p)

            ### CHOIX D'UNE OPTION

            choix_table = [f"""<label for="{table}">{table}</label><input type="radio" name="table" value="{table}" id="{table}" >""" for table in Tables.keys()]

            r += f"""<hr /><br />
                    <form action="admin?pwd={GLOBAL_PASSWORD}" method="post">
                        <div>
                            <fieldset><legend>Voir une table</legend>
                                Table : {" / ".join(choix_table)}
                                <input type="submit" name="viewtable", value="Voir la table">
                            </fieldset>
                            <br />
                            <fieldset><legend>Options Alwaysdata</legend>
                                <label for="restart_site">Restart le site :</label> <input type="submit" name="restart_site" id="restart_site" value="Restart">
                            </fieldset>
                            <br />
                            <fieldset><legend>Tâches planifiées</legend>
                                <input type="submit" name="viewcron" id="viewcron" value="Voir les tâches"> <br />

                                <label for="job">Tâche :</label> <select name="job" id="job">{"".join([f"<option value='{j}'>{j}</option>" for j in jobs])}</select> /
                                <label for="heure">Heure (si *_action) :</label> <input type="number" name="heure" id="heure" min=0 max=23> /
                                <label for="test">Mode test</label> <input type="checkbox" name="test" id="test"> /
                                <input type="submit" name="sendjob" value="Envoyer"> <br/><br/>

                                <label for="d">Consulter les logs du : </label> <input type="number" name="d" id="d" min=1 max=31 value={time.strftime('%d')}>/<input type="number" name="m" id="m" min=1 max=12 value={time.strftime('%m')}>/<input type="number" name="Y" id="Y" min=2020 max={time.strftime('%Y')} value={time.strftime('%Y')}>
                                <input type="submit" name="viewlogs" value="Lire">
                            </fieldset>
                        </div>
                    </form>
                 """

            ### ARGUMENTS BRUTS (pour débug)

            r += f"""<br/><hr/><br/>
                <div>
                    <i>
                        GET args:{dict(d)} <br/>
                        POST args:{dict(p)}
                    </i>
                </div>"""

        else:
            raise ValueError("WRONG OR MISSING PASSWORD!")

    except Exception:
        r += infos_tb()     # Affiche le "traceback" (infos d'erreur Python) en cas d'erreur (plutôt qu'un 501 Internal Server Error)

    finally:
        return r
