from __init__ import db, cache_TDB
from sqlalchemy.exc import *        # Exceptions générales SQLAlchemy
from sqlalchemy.orm.exc import *    # Exceptions requêtes SQLAlchemy
from sqlalchemy.orm.attributes import flag_modified
from flask import abort

import blocs.chatfuel as chatfuel
import blocs.gsheets as gsheets
import string, random
import sys, traceback

import requests, json


GLOBAL_PASSWORD = "C'estSuperSecure!"


### UTILITAIRES

def strhtml(r):
    return r.replace('&','&esp;').replace('\n', '<br/>').replace('<','&lt;').replace('>','&gt;')

def infos_tb(quiet=False):
    tb = strhtml("".join(traceback.format_exc()))
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


### sync_TDB

def sync_TDB(d):    # d : pseudo-dictionnaire des arguments passés en GET (juste pour pwd, normalement)
    r = ""
    try:
        verbose = ('v' in d)
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
                                


            ### MODIFICATIONS DANS CHATFUEL DIRECT
            
            if Modified_ids != []:
                BOT_ID = "5be9b3b70ecd9f4c8cab45e0"
                CHATFUEL_TOKEN = "mELtlMAHYqR0BvgEiMq8zVek3uYUK3OJMbtyrdNPTrQB9ndV0fM7lWTFZbM4MZvD"
                CHATFUEL_TAG = "CONFIRMED_EVENT_UPDATE"
                
                params_r = {"chatfuel_token" : CHATFUEL_TOKEN,
                            "chatfuel_message_tag" : CHATFUEL_TAG,
                            "chatfuel_block_name" : "Sync"}
                        
                for id in Modified_ids:
                    
                    attrs = {}
                    for (idM, col, v) in Modifs:
                        if id == idM:
                            attrs[col] = v
                            attrs[f"sync_{col}"] = True
                            
                    params = format_Chatfuel(attrs)
                    for k,v in params_r.items():
                        params[k] = v
                        
                    url_params = "&".join([f"{k}={v}" for k,v in params.items()])
                    
                    rep = requests.post(f"https://api.chatfuel.com/bots/{BOT_ID}/users/{id}/send?{url_params}")
                    rep = rep.json()
                    
                    if "code" in rep:
                        raise Exception("Erreur d'envoi Chatfuel Broadcast API. Réessaie.")
                    else:
                        if not rep["success"]:
                            pass
                            # raise Exception(f"Chatfuel Broadcast API a renvoyé une erreur : {rep["result"]}")


            ### APPLICATION DES MODIFICATIONS SUR LE TDB
            
            # Convertit ID et colonne en indices lignes et colonnes (à partir de 0)
            if Modifs != []:
                Modifs_rdy = []
                lm = 0
                cm = 0
                for (id, col, v) in Modifs:
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
            
            tous = cache_TDB.query.all()     # Liste des joueurs tels qu'actuellement en cache
            NT = len(tous)
            
            if "type" in d and d["type"] == "vivants":
                rep = cache_TDB.query.filter(cache_TDB.statut != "mort").order_by(cache_TDB.nom).all()
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
            return chatfuel.ErrorReport(exc, verbose=verbose, message="Une erreur technique est survenue 😪\nMerci d'en informer les MJs ! Erreur :")
        
    else:
        return chatfuel.Response(R)

    



### OPTIONS DU PANNEAU D'ADMIN

exec(open("./blocs/admin_options.py").read())



### PANNEAU D'ADMIN

# Options d'administration automatiques (ajout,...) - pour tests/debug seulement !
def manual(d):
    return admin(d, d)
    
def admin(d, p):    # d : pseudo-dictionnaire des arguments passés en GET (pwd notemment) ; p : idem pour les arguments POST (différentes options du panneau)
    try:
        r = "<h1>« Panneau d'administration » (vaguement, hein) LG Rez</h1><hr/>"

        if ("pwd" in d) and (d["pwd"] == GLOBAL_PASSWORD):      # Vérification mot de passe

            ### COMPORTEMENT OPTION
            
            if "additem" in p:
                r += additem(d, p)
                r += viewtable(d, p)

            if "delitem" in p:
                r += delitem(d, p)
                r += viewtable(d, p)

            if "viewtable" in p:
                r += viewtable(d, p)
                
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

            
            if "testupdate" in d:
                
                r += "<br/>TEST UPDATE 44444444<br/>"
                
                user_cache = cache_TDB.query.filter_by(messenger_user_id=44444444).first()
                user_cache.nom = "BONSOIR"
                db.session.commit()
            
            if "oskour" in d:
                r += "OSKOUR<br/>"
                db.session.rollback()
                r += "OSKOUUUUR<br/>"
            

            ### CHOIX D'UNE OPTION
                
            r += f"""<hr/><br />
                    <form action="admin?pwd={GLOBAL_PASSWORD}" method="post">
                        <div>
                            <fieldset>
                                <legend>Voir une table</legend>
                                Table : 
                                <label for="cache_TDB">cache_TDB </label> <input type="radio" name="table" value="cache_TDB" id="cache_TDB"> / 
                                <!-- <label for="cache_Chatfuel">cache_Chatfuel </label> <input type="radio" name="table" value="cache_Chatfuel" id="cache_Chatfuel"> -->
                                <input type="submit" name="viewtable", value="Voir la table">
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

            BOT_ID = "5be9b3b70ecd9f4c8cab45e0"
            CHATFUEL_TOKEN = "mELtlMAHYqR0BvgEiMq8zVek3uYUK3OJMbtyrdNPTrQB9ndV0fM7lWTFZbM4MZvD"
            CHATFUEL_TAG = "CONFIRMED_EVENT_UPDATE"
            id = 2033317286706583
            bloc = d["bloc"] if "bloc" in d else "Sync"
            
            
            params = {"chatfuel_token" : CHATFUEL_TOKEN,
                      "chatfuel_message_tag" : CHATFUEL_TAG,
                      "chatfuel_block_name" : bloc}
                      
            for k,v in d.items():
                if k[:4] == "sync":
                    params[k] = v
                    
            r += f"Requête : <pre>{json.dumps(params, indent=4)}</pre>"
            
            url_params = "&".join([f"{k}={v}" for k,v in params.items()])
            
            rep = requests.post(f"https://api.chatfuel.com/bots/{BOT_ID}/users/{id}/send?{url_params}")
            r += f"<br /><br />Réponse : <pre>{rep.text}</pre>"

        else:
            raise ValueError("WRONG OR MISSING PASSWORD!")

    except Exception:
        r += infos_tb()     # Affiche le "traceback" (infos d'erreur Python) en cas d'erreur (plutôt qu'un 501 Internal Server Error)

    finally:
        return r
