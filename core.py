import sys
import time
import traceback
import string
import random
import requests
import json

from sqlalchemy.exc import *        # Exceptions générales SQLAlchemy
from sqlalchemy.orm.exc import *    # Exceptions requêtes SQLAlchemy
from sqlalchemy.orm.attributes import flag_modified
from flask import abort

from __init__ import db, cache_TDB
import blocs.chatfuel as chatfuel
import blocs.gsheets as gsheets


GLOBAL_PASSWORD = "CestSuperSecure"

BOT_ID = "5be9b3b70ecd9f4c8cab45e0"
CHATFUEL_TOKEN = "mELtlMAHYqR0BvgEiMq8zVek3uYUK3OJMbtyrdNPTrQB9ndV0fM7lWTFZbM4MZvD"
CHATFUEL_TAG = "CONFIRMED_EVENT_UPDATE"

ALWAYSDATA_API_KEY = "f73dc3407a1949a8b0a7efd1b374f9c4"

jobs = ["open_cond", "remind_cond", "close_cond",
        "open_maire", "remind_maire", "close_maire",
        "open_loups", "remind_loups", "close_loups",
        "open_action", "remind_action", "close_action",
        ]

MAX_TRIES = 5


### UTILITAIRES

def strhtml(r):
    return r.replace('&','&esp;').replace('\n', '<br/>').replace('<','&lt;').replace('>','&gt;')

def html_escape(r):
    return str(r).replace('&','&esp;').replace('<','&lt;').replace('>','&gt;')

def infos_tb(quiet=False):
    tb = traceback.format_exc()
    if quiet:
        return tb
    else:
        return f"<br/><div> AN EXCEPTION HAS BEEN RAISED! <br/><pre>{tb}</pre></div>"

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def transtype(value, col, SQL_type, nullable):      # Utilitaire : type un input brut (POST, GET, JSON de Chatfuel...) selon le type de sa colonne
    try:
        if value in (None, '', 'None', 'none', 'Null', 'null', 'not set', 'non défini'):
            if nullable:
                return None
            else:
                raise ValueError
        elif SQL_type == "String":
            return str(value)
        elif SQL_type in ("Integer", "BigInteger"):
            return int(value)
        elif SQL_type == "Boolean":
            if value in [1, '1', True, 'true', 'True', 'TRUE', 'vrai', 'Vrai', 'VRAI']:
                return True 
            elif value in [0, '0', False, 'false', 'False', 'FALSE', 'faux', 'Faux', 'FAUX']:
                return False
            else:
                raise ValueError()
        else:
            raise KeyError(f"unknown column type for column '{col}': '{SQL_type}''")
    except (ValueError, TypeError):
        raise ValueError(f"Valeur '{value}' incorrecte pour la colonne '{col}' (type '{SQL_type}'/{'NOT NULL' if not nullable else ''})")

def format_Chatfuel(d):         # Représentation des attributs dans Chatfuel
    for k,v in d.items():
        if v == True:
            d[k] = 1
        elif v == False:
            d[k] = 0
        elif v == None:
            d[k] = "non défini"
    return d

def getjobs():                  # Récupère la liste des tâches planifiées sur l'API alwaysdata
    rep = requests.get('https://api.alwaysdata.com/v1/job/', auth=(ALWAYSDATA_API_KEY, ''))
    
    if rep:
        try:
            lst = rep.json()
        except:
            lst = []
    else:
        raise ValueError(f"Request Error (HTTP code {rep.status_code})")
        
    return lst

### sync_TDB

def sync_TDB(d):    # d : pseudo-dictionnaire des arguments passés en GET (juste pour pwd, normalement)
    r = ""
    try:
        verbose = ('v' in d)        # Messages d'erreur/... détaillés
        silent = ('s' in d)         # Ne prévient pas les joueurs des modifications
        if verbose:
            r += "sync_TDB:"
            
        if ("pwd" in d) and (d["pwd"] == GLOBAL_PASSWORD):      # Vérification mot de passe
            
            ### GÉNÉRALITÉS
            
            cols = [str(column.key) for column in cache_TDB.__table__.columns]      # Colonnes de cache_TDB
            cols_SQL_types = {col:type(getattr(cache_TDB, col).property.columns[0].type).__name__ for col in cols}
            cols_SQL_nullable = {col:getattr(cache_TDB, col).property.columns[0].nullable for col in cols}
            
            
            ### RÉCUPÉRATION INFOS GSHEET
            
            workbook = gsheets.connect("1D5AWRmdGRWzzZU9S665U7jgx7U5LwvaxkD8lKQeLiFs")  # Tableau de bord
            sheet = workbook.worksheet("Journée en cours")
            values = sheet.get_all_values()     # Liste de liste des valeurs
            (NL, NC) = (len(values), len(values[0]))
            
            if verbose:
                r += f"<{NL}L/{NC}C>\n"
                
            head = values[2]
            TDB_index = {col:head.index(col) for col in cols}    # Dictionnaire des indices des colonnes GSheet pour chaque colonne de la table
            TDB_tampon_index = {col:head.index("tampon_"+col) for col in cols if col != 'messenger_user_id'}    # Idem pour la partie « tampon »
            
            
            # CONVERSION INFOS GSHEET EN UTILISATEURS
            
            users_TDB = []              # Liste des joueurs tels qu'actuellement dans le TDB
            ids_TDB = []                # messenger_user_ids des différents joueurs du TDB
            rows_TDB = {}               # Indices des lignes ou sont les différents joueurs du TDB
            
            for l in range(NL):
                L = values[l]
                id = L[TDB_index["messenger_user_id"]]
                if (id != "") and RepresentsInt(id):
                    
                    joueur = {col:transtype(L[TDB_index[col]], col, cols_SQL_types[col], cols_SQL_nullable[col]) for col in cols}
                    user_TDB = cache_TDB(**joueur)
                    
                    users_TDB.append(user_TDB)
                    ids_TDB.append(user_TDB.messenger_user_id)
                    rows_TDB[user_TDB.messenger_user_id] = l
                    
                    
            ### RÉCUPÉRATION UTILISATEURS CACHE
            
            users_cache = cache_TDB.query.all()     # Liste des joueurs tels qu'actuellement en cache
            ids_cache = [user_cache.messenger_user_id for user_cache in users_cache]
            
            
            ### COMPARAISON
            
            Modifs = []         # Modifs à porter au TDB : tuple (id - colonne (nom) - valeur)
            Modified_ids = []
            
            for user_cache in users_cache.copy():                      ## 1. Joueurs dans le cache supprimés du TDB
                if user_cache.messenger_user_id not in ids_TDB:
                    users_cache.remove(user_cache)
                    db.session.delete(user_cache)
                    
                    # On doit également le supprimer de cache_Chatfuel
                    # user_cC = cache_Chatfuel.query.filter_by(messenger_user_id=user_cache.messenger_user_id).first()
                    # db.session.delete(user_cC)
                    
                    if verbose:
                        r += f"\nJoueur dans les caches hors TDB : {user_cache}"
                        
            for user_cache in users_TDB:                               ## 2. Joueurs dans le TDB pas encore dans le cache
                if user_cache.messenger_user_id not in ids_cache:
                    if verbose:
                        r += f"\nJoueur dans le TDB hors caches : {user_cache}"
                        
                    users_cache.append(user_cache)
                    db.session.add(user_cache)
                    id = user_cache.messenger_user_id
                    
                    # On doit également l'ajouter à cache_Chatfuel
                    # user_cC = cache_Chatfuel(**{col:getattr(user_cache, col) for col in cols})     # Mêmes attributs que user_cache
                    # db.session.add(user_cC)
                        
                    # Validation dans le TDB
                    Modifs.extend( [( id, col, getattr(user_cache, col) ) for col in cols if col != 'messenger_user_id'] )    # Sans le _EAT parce qu'a priori le joueur est ajouté au TDB avec ses attributs déjà existants
                    
            # À ce stade, on a les même utilisateurs dans users_TDB et users_cache (mais pas forcément les mêmes infos !)
            
            for user_TDB in users_TDB:                           ## 3. Différences
                user_cache = [user for user in users_cache if user.messenger_user_id==user_TDB.messenger_user_id][0]    # user correspondant dans le cache
                    
                if user_cache != user_TDB:     # Au moins une différence !
                    if verbose:
                        r += f"\nJoueur différant entre TDB et cache_TDB : {user_TDB}"
                    id = user_TDB.messenger_user_id
                    
                    for col in cols:
                        if getattr(user_cache, col) != getattr(user_TDB, col):
                            if verbose:
                                r += f"\n---- Colonne différant : {col} (TDB : {getattr(user_TDB, col)}, cache_TDB : {getattr(user_cache, col)})"
                                
                            setattr(user_cache, col, getattr(user_TDB, col))
                            flag_modified(user_cache, col)
                            # Modifs.append( ( id, col, str(getattr(user_TDB, col))+"_EAT" ) )
                            Modifs.append( ( id, col, getattr(user_TDB, col) ) )        # Avec le passage direct à Chatfuel, plus besoin de _EAT. La modif ne sera indiquée dans le TDB que si tout est successful.
                            if id not in Modified_ids:
                                Modified_ids.append(id)
                                


            ### MODIFICATIONS DANS CHATFUEL DIRECT (envoi d'un message aux gens)
            
            if Modified_ids:
                params_r = {"chatfuel_token" : CHATFUEL_TOKEN,
                            "chatfuel_message_tag" : CHATFUEL_TAG,
                            "chatfuel_block_name" : "Sync_silent" if silent else "Sync"}
                        
                for id in Modified_ids:
                    
                    attrs = {}
                    for (idM, col, v) in Modifs:
                        if id == idM:
                            attrs[col] = v
                            if not silent:
                                attrs[f"sync_{col}"] = True
                            
                    params = format_Chatfuel(attrs)
                    for k,v in params_r.items():
                        params[k] = v
                        
                    rep = requests.post(f"https://api.chatfuel.com/bots/{BOT_ID}/users/{id}/send", params=params)
                    rep = rep.json()
                    
                    if "code" in rep:
                        raise Exception("Erreur d'envoi Chatfuel Broadcast API. Réessaie.")
                    else:
                        if not rep["success"]:
                            pass
                            # raise Exception(f"""Chatfuel Broadcast API a renvoyé une erreur : {rep["result"]}""")


            ### APPLICATION DES MODIFICATIONS SUR LE TDB
            
            if Modifs:
                Modifs_rdy = []
                lm = 0
                cm = 0
                for (id, col, v) in Modifs:
                    # Convertit ID et colonne en indices lignes et colonnes (à partir de 0)
                    l = rows_TDB[id]
                    if l > lm:
                        lm = l
                    c = TDB_tampon_index[col]     # Modification de la partie « tampon » du TDB
                    if c > cm:
                        cm = c
                    if v == None:
                        v = '' 
                    elif v == "None_EAT":
                        v = "_EAT"
                    elif v == "None":
                        v = ""
                    Modifs_rdy.append((l, c, v))
                
                # Récupère toutes les valeurs sous forme de cellules gspread
                cells = sheet.range(1, 1, lm+1, cm+1)   # gspread indexe à partir de 1 (comme les gsheets)
                # raise KeyError(str(cells)) 
                # raise KeyError(f"{lm}/{cm}")
                # a = ""
                cells_to_update = []
                for (l, c, v) in Modifs_rdy:
                    cell = [cell for cell in filter(lambda cell:cell.col == c+1 and cell.row == l+1, cells)][0]
                    cell.value = v       # cells : ([<L1C1>, <L1C2>, ..., <L1Ccm>, <L2C1>, <L2C2>, ..., <LlmCcm>]
                    cells_to_update.append(cell)
                    # a += f"lm:{lm}/cm:{cm} - l:{l}/c:{c} - .row:{cell.row}/.col:{cell.col}\n"
                    
                # raise KeyError(a)
                sheet.update_cells(cells_to_update)
                
                if verbose:
                    r += "\n\n" + "\n".join([str(m) for m in Modifs])
                        
                        
            ### APPLICATION DES MODIFICATIONS SUR LES BDD cache
            
            db.session.commit()     # Modification de cache_TDB
            
            
            ### FIN DE LA PROCÉDURE
            
        else:
            raise ValueError("WRONG OR MISSING PASSWORD!")
            
    except Exception as e:
        db.session.rollback()
        return (400, f"{type(e).__name__}({str(e)})")     # Affiche le "traceback" (infos d'erreur Python) en cas d'erreur (plutôt qu'un 501 Internal Server Error)
        # return (400, "".join(traceback.format_exc()))     # Affiche le "traceback" (infos d'erreur Python) en cas d'erreur (plutôt qu'un 501 Internal Server Error) 
        
    else:
        return r


### LISTE MORTS ET VIVANTS

def liste_joueurs(d):    # d : pseudo-dictionnaire des arguments passés en GET (pwd, type)
    R = []  # Liste des blocs envoyés en réponse
    try:
        if ("pwd" in d) and (d["pwd"] == GLOBAL_PASSWORD):      # Vérification mot de passe
            
            tous = cache_TDB.query.filter(cache_TDB.statut.in_(["vivant","MV","mort"])).all()     # Liste des joueurs tels qu'actuellement en cache
            NT = len(tous)
            
            if "type" in d and d["type"] == "vivants":
                rep = cache_TDB.query.filter(cache_TDB.statut.in_(["vivant","MV"])).order_by(cache_TDB.nom).all()
                descr = "en vie"
                bouton_text = "Joueurs morts ☠"
                bouton_bloc = "Joueurs morts"
            elif "type" in d and d["type"] == "morts":
                rep = cache_TDB.query.filter(cache_TDB.statut == "mort").order_by(cache_TDB.nom).all()
                descr = "morts" 
                bouton_text = "Joueurs en vie 🕺"
                bouton_bloc = "Joueurs en vie"
            else:
                raise ValueError('GET["type"] must be "vivants" or "morts"')
                
            NR = len(rep)
            if NR > 0:
                R.append(chatfuel.Text(f"Liste des {NR}/{NT} joueurs {descr} :"))
                LJ = [u.nom for u in rep]
            else:
                LJ = ["Minute, papillon !"]
            
            R.append(chatfuel.Text('\n'.join(LJ)).addQuickReplies([chatfuel.Button("show_block", bouton_text, bouton_bloc),
                                                                    chatfuel.Button("show_block", "Retour menu 🏠", "Menu")]))
            
        else:
            raise ValueError("WRONG OR MISSING PASSWORD!")
            
    except Exception as exc:
        db.session.rollback()
        if type(exc).__name__ == "OperationalError":
            return chatfuel.ErrorReport(Exception("Impossible d'accéder à la BDD, réessaie ! (souvent temporaire)"), verbose=verbose, message="Une erreur technique est survenue 😪\n Erreur :")
        else:
            return chatfuel.ErrorReport(exc, message="Une erreur technique est survenue 😪\nMerci d'en informer les MJs ! Erreur :")
        
    else:
        return chatfuel.Response(R)


### APPEL D'UNE TÂCHE PLANIFIÉE

def cron_call(d):
    r = ""
    log = ""
    try:
        verbose = ("v" in d)
        testmode = ("test" in d)
        
        if ("pwd" in d) and (d["pwd"] == GLOBAL_PASSWORD):      # Vérification mot de passe
            
            ### GÉNÉRALITÉS
            
            def get_criteres(job):
                if job.endswith("cond") or job.endswith("maire"):
                    return {"inscrit": True, "votantVillage": True}
                elif job.endswith("loups"):
                    return {"inscrit": True, "votantLoups": True}
                elif job.endswith("action"):
                    if ("heure" in d) and RepresentsInt(d["heure"]):
                        heure = int(d["heure"]) % 24
                    else:
                        if job.startswith("remind"):
                            heure = (int(time.strftime("%H")) + 1) % 24
                        else:
                            heure = int(time.strftime("%H"))
                    if job.startswith("open"):
                        return {"inscrit": True, "roleActif": True, "debutRole": heure}
                    else:
                        return {"inscrit": True, "roleActif": True, "finRole": heure}
                else:
                    raise ValueError(f"""Cannot associate criteria to job {job}""")
                    
                    
            ### DÉTECTION TÂCHE À FAIRE ET CRITÈRES ASSOCIÉS
            
            log +=  f"> {time.ctime()} (verbose={verbose}, testmode={testmode}) – "
            
            if ("job" in d) and (d["job"] in jobs):         # jobs : défini en début de fichier, car utile dans admin
                job = d["job"]
                if verbose:
                    r += f"""Job : <code>{job}</code><br/>"""
                    
                log +=  f"job : {job} -> "
                
                criteres = get_criteres(job)
                if verbose:
                    r += f"""Critères : <code>{html_escape(criteres)}</code><br/>"""
                    
                if testmode:
                    criteres_test = {"messenger_user_id": 2033317286706583}   # Loïc, pour tests
                    if verbose:
                        r += f"""Critères MODE TEST, réellement appliqués : <code>{html_escape(criteres_test)}</code><br/>"""
                        
            else:
                raise ValueError("""Bad usage: required argument "job" not in GET or incorrect""")
                
                
            ### RÉCUPÉRATION UTILISATEURS CACHE
            
            users = cache_TDB.query.filter_by(**criteres).all()     # Liste des joueurs répondant aux cirtères
            if verbose:
                str_users = str(users).replace(', ', ',\n ')
                r += f"<br/>Utilisateur(s) répondant aux critères ({len(users)}) : <pre>{html_escape(str_users)}</pre>"

            if testmode:
                users = cache_TDB.query.filter_by(**criteres_test).all()    # on écrase par les utilisateur MODE TEST
                if verbose:
                    str_users = str(users).replace(', ',',\n ')
                    r += f"<br/>Utilisateur(s) répondant aux critères MODE TEST ({len(users)}) : <pre>{html_escape(str_users)}</pre>"
                    
            log += f"{len(users)} utilisateurs trouvés\n"
            
            
            ### MODIFICATIONS DANS CHATFUEL DIRECT
            
            if users:
                params = {"chatfuel_token": CHATFUEL_TOKEN,
                          "chatfuel_message_tag": CHATFUEL_TAG,
                          "chatfuel_block_name": "Tâche planifiée",
                          "job": job
                          }
                          
                for user in users:
                    rep = False
                    tries = 0
                    while (not rep) and (tries < MAX_TRIES):
                        rep = requests.post(f"https://api.chatfuel.com/bots/{BOT_ID}/users/{user.messenger_user_id}/send", params=params)
                        tries += 1
                        if not rep:
                            time.sleep(5)
                            
                    if tries == MAX_TRIES:
                        log += f"    - !!! Impossible d'envoyer à l'utilisateur {user} ({MAX_TRIES} tentatives)" 
                        if verbose:
                            r += f"<br/>!!! Impossible d'envoyer le job <code>{job}</code> à l'utilisateur <code>{html_escape(user)}</code> ({MAX_TRIES} tentatives)"
                        continue
                        
                    rep = rep.json()
                    
                    if verbose:
                        r += f"<br/>Envoi job <code>{job}</code> à l'utilisateur <code>{html_escape(user)}</code> – {tries} tentative(s)"
                        
                    log +=  f"    - Envoi à {user} : OK, {tries} tentative(s)\n"
                    
                    if "code" in rep:
                        raise Exception("Erreur d'envoi Chatfuel Broadcast API. Réessaie.")
                    else:
                        if not rep["success"]:
                            raise Exception(f"""Chatfuel Broadcast API a renvoyé une erreur : {rep["result"]}""")

            ### FIN DE LA PROCÉDURE
            
            log += "\n"
            
        else:
            raise ValueError("WRONG OR MISSING PASSWORD!")
            
    except Exception as e:
        log += f"\n> {time.ctime()} - Error, exiting:\n{traceback.format_exc()}\n\n"
        
        if verbose:
            if "return_tb" in d:
                return traceback.format_exc()
            else:
                return (400, "".join(traceback.format_exc()))     # Affiche le "traceback" (infos d'erreur Python) en cas d'erreur (plutôt qu'un 501 Internal Server Error) 
        else:
            return (400, f"{type(e).__name__}({str(e)})")     # Affiche le "traceback" (infos d'erreur Python) en cas d'erreur (plutôt qu'un 501 Internal Server Error)

    else:
        return r
        
    finally:
        with open(f"logs/cron_call/{time.strftime('%Y-%m-%d')}.log", 'a+') as f:
            f.write(log)



### OPTIONS DU PANNEAU D'ADMIN

exec(open("./blocs/admin_options.py").read())



### PANNEAU D'ADMIN

# Options d'administration automatiques (ajout,...) - pour tests/debug seulement !
def manual(d):
    return admin(d, d)
    
def admin(d, p):    # d : pseudo-dictionnaire des arguments passés en GET (pwd notemment) ; p : idem pour les arguments POST (différentes options du panneau)
    r = ""
    try:
        if ("pwd" in d) and (d["pwd"] == GLOBAL_PASSWORD):      # Vérification mot de passe
            r += f"""<h1><a href="admin?pwd={GLOBAL_PASSWORD}">Panneau d'administration LG Rez</a></h1><hr/>"""

            ### BASE DE DONNÉES
            
            if "viewtable" in p:
                r += viewtable(d, p)
            
            if "additem" in p:
                r += additem(d, p)
                r += viewtable(d, p)

            if "delitem" in p:
                r += delitem(d, p)
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
                r += "<p>values:" + strhtml(str(type(values))) + "</p>"
                r += "<p>values[8]:" + strhtml(str(type(values[8]))) + "</p>"
                r += "<p>values[8][8]:" + strhtml(values[8][8]) + "</p><br /><br />"
                
                val = sheet.cell(8, 8)
                r += "<p>val:" + strhtml(str(type(val))) + "</p>"
                r += "<p>val.value:" + strhtml(str(type(val.value))) + "</p>"
                r += "<p>dir(val):" + strhtml(str(dir(val))) + "</p><br /><br />"
                
            if "oskour" in d:
                r += "OSKOUR<br/>"
                db.session.rollback()
                r += "OSKOUUUUR<br/>"
                
                
            ### STATUTS
                
            if ("statuts" in p) or (not p):   # si statuts demandés, ou si rien passé en POST
                r += f"<br />{time.ctime()} – Statuts :"
                
                # On récupère les tâches planifiées
                lst = getjobs()
                    
                taches = {}
                for job in jobs:
                    taches[job] = [j for j in lst if job in j["argument"]]      # toutes les tâches liées au job donné
                    
                def phrase(tchs):
                    critere = all([j["is_disabled"] for j in tchs])         # toutes tâches désactivées
                    
                    def red(s):    return f"<font color='red'><b>{s}</b></font>"
                    def green(s):  return f"<font color='green'><b>{s}</b></font>"
                    
                    ids = ','.join([str(t["id"]) for t in tchs])
                    url = f"admin?pwd={GLOBAL_PASSWORD}&disablecron&id={ids}"
                    
                    return f"""{red("Désactivé") if critere else green("Activé")} – {f"<a href='{url}'>Activer</a>" if critere else f"<a href='{url}&disable'>Désactiver</a>"}"""
                    
                r += f"""<ul>
                        <li>Vote condamné (Lu-Ve) :
                            <ul>
                                <li>Ouverture : {phrase(taches["open_cond"])}</li>
                                <li>Fermeture : {phrase(taches["remind_cond"] + taches["close_cond"])}</li>
                            </ul>
                        </li><br />
                        <li>Vote maire :
                            <ul>
                                <li>Ouverture : {phrase(taches["open_maire"])}</li>
                                <li>Fermeture : {phrase(taches["remind_maire"] + taches["close_maire"])}</li>
                            </ul>
                        </li><br />
                        <li>Vote loups (Di-Je) :
                            <ul>
                                <li>Ouverture : {phrase(taches["open_loups"])}</li>
                                <li>Fermeture : {phrase(taches["remind_loups"] + taches["close_loups"])}</li>
                            </ul>
                        </li><br />
                        <li>Actions de rôle (Lu-Ve 0-18h + Di-Je 19-23h) :
                            <ul>
                                <li>Ouverture : {phrase(taches["open_action"])}</li>
                                <li>Fermeture : {phrase(taches["remind_action"] + taches["close_action"])}</li>
                            </ul>
                        </li></ul><br />"""
                        
                        
                        
            ### CHOIX D'UNE OPTION
            
            r += f"""<hr /><br />
                    <form action="admin?pwd={GLOBAL_PASSWORD}" method="post">
                        <div>
                            <fieldset><legend>Voir une table</legend>
                                Table :     
                                <label for="cache_TDB">cache_TDB </label> <input type="radio" name="table" value="cache_TDB" id="cache_TDB" checked> 
                                <input type="submit" name="viewtable", value="Voir la table">
                            </fieldset>
                            <br />
                            <fieldset><legend>Options Alwaysdata</legend>
                                <label for="restart_site">Restart le site :</label> <input type="submit" name="restart_site" id="restart_site" value="Restart">
                            </fieldset>
                            <br />
                            <fieldset><legend>Tâches planifiées</legend>
                                <input type="submit" name="viewcron" id="viewcron" value="Voir les tâches"> <br />
                                
                                <label for="job">Tâche :</label> <select name="job" id="job">{''.join([f"<option value='{j}'>{j}</option>" for j in jobs])}</select> / 
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




def API_test(d):
    """ Récupère et renvoie une information à Chatfuel """

    try:
        # user_TDB = cache_TDB(messenger_user_id = random.randrange(1000000000),
        #                     inscrit = True,
        #                     nom = d["a_creer"],
        #                     chambre = random.randrange(101,800),
        #                     statut = "test",
        #                     role = "rôle"+str(random.randrange(15)),
        #                     camp = "camp"+str(random.randrange(3)),
        #                     votantVillage = random.randrange(1),
        #                     votantLoups = random.randrange(1))
        # 
        # db.session.add(user_TDB)
        # db.session.commit()
        # 
        # cont = [e.nom for e in cache_TDB.query.all()]

        rep= chatfuel.Response([    chatfuel.Text("Max length test :"),
                                    # chatfuel.Buttons("Oui", [
                                    #     chatfuel.Button("show_block", "Go menu", "Menu"),
                                    #     chatfuel.Button("web_url", "J'adore", "https://lmfgtf.com")
                                    #     ]),
                                    chatfuel.Text("Parfait. Doublement parfait.")
                                    ],
                                set_attributes={"a":1,"b":2}#,
                                # redirect_to_blocks="Menu"
                                )

    except Exception as exc:
        rep = chatfuel.ErrorReport(exc)

    finally:
        return rep


def Hermes_test(d):
    r = "<h1>Hermes test.</h1><hr/><br/>"
    try:

        if ("pwd" in d) and (d["pwd"] == GLOBAL_PASSWORD):      # Vérification mot de passe

            ### COMPORTEMENT OPTION

            id = 2033317286706583
            bloc = d["bloc"] if "bloc" in d else "Sync"
                        
            params = {"chatfuel_token" : CHATFUEL_TOKEN,
                      "chatfuel_message_tag" : CHATFUEL_TAG,
                      "chatfuel_block_name" : bloc}
                      
            for k,v in d.items():
                if k[:4] == "sync":
                    params[k] = v
                    
            r += f"Requête : <pre>{json.dumps(params, indent=4)}</pre>"
            
            rep = requests.post(f"https://api.chatfuel.com/bots/{BOT_ID}/users/{id}/send", params=params)
            r += f"<br /><br />Réponse : <pre>{rep.text}</pre>"

        else:
            raise ValueError("WRONG OR MISSING PASSWORD!")

    except Exception:
        r += infos_tb()     # Affiche le "traceback" (infos d'erreur Python) en cas d'erreur (plutôt qu'un 501 Internal Server Error)

    finally:
        return r
