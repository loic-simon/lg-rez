from __init__ import db, cache_TDB, cache_Chatfuel
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
        return "<br/><div> AN EXCEPTION HAS BEEN RAISED! <br/><pre>{}</pre></div>".format(tb)

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
            raise KeyError("unknown column type for column '{}': '{}''".format(col, SQL_type))
    except (ValueError, TypeError):
        raise ValueError("Valeur '{}' incorrecte pour la colonne '{}' (type '{}'/{})".format(value, col, SQL_type, 'NOT NULL' if not nullable else ''))

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
            cols_SQL_nullable = {col:getattr(cache_Chatfuel, col).property.columns[0].nullable for col in cols}
            
            ### RÉCUPÉRATION INFOS GSHEET
            
            workbook = gsheets.connect("1D5AWRmdGRWzzZU9S665U7jgx7U5LwvaxkD8lKQeLiFs")  # Tableau de bord
            sheet = workbook.worksheet("Journée en cours")
            values = sheet.get_all_values()     # Liste de liste des valeurs
            (NL, NC) = (len(values), len(values[0]))
            
            if verbose:
                r += "<{}L/{}C>\n".format(NL, NC)
                
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
            
            users_cT = cache_TDB.query.all()     # Liste des joueurs tels qu'actuellement en cache
            ids_cT = [user_cT.messenger_user_id for user_cT in users_cT]
                    
                
            ### COMPARAISON
            
            Modifs = []         # Modifs à porter au TDB : tuple (id - colonne (nom) - valeur)
            Modified_ids = []
            
            for user_cT in users_cT.copy():                      ## 1. Joueurs dans le cache supprimés du TDB
                if user_cT.messenger_user_id not in ids_TDB:
                    users_cT.remove(user_cT)
                    db.session.delete(user_cT)
                    
                    # On doit également le supprimer de cache_Chatfuel
                    user_cC = cache_Chatfuel.query.filter_by(messenger_user_id=user_cT.messenger_user_id).first()
                    db.session.delete(user_cC)
                    
                    if verbose:
                        r += "\nJoueur dans les caches hors TDB : {}".format(user_cT)
                        
            for user_cT in users_TDB:                               ## 2. Joueurs dans le TDB pas encore dans le cache
                if user_cT.messenger_user_id not in ids_cT:
                    if verbose:
                        r += "\nJoueur dans le TDB hors caches : {}".format(user_cT)
                        
                    users_cT.append(user_cT)
                    db.session.add(user_cT)
                    id = user_cT.messenger_user_id
                    
                    # On doit également l'ajouter à cache_Chatfuel
                    user_cC = cache_Chatfuel(**{col:getattr(user_cT, col) for col in cols})     # Mêmes attributs que user_cT
                    db.session.add(user_cC)
                        
                    # Validation dans le TDB
                    Modifs.extend( [( id, col, getattr(user_cT, col) ) for col in cols if col != 'messenger_user_id'] )    # Sans le _EAT parce qu'a priori le joueur est ajouté au TDB avec ses attributs déjà existants
                    
            # À ce stade, on a les même utilisateurs dans users_TDB et users_cT (mais pas forcément les mêmes infos !)
            
            for user_TDB in users_TDB:                           ## 3. Différences
                user_cT = [user for user in users_cT if user.messenger_user_id==user_TDB.messenger_user_id][0]    # user correspondant dans le cache
                    
                if user_cT != user_TDB:     # Au moins une différence !
                    if verbose:
                        r += "\nJoueur différant entre TDB et cache_TDB : {}".format(user_TDB)
                    id = user_TDB.messenger_user_id
                    
                    for col in cols:
                        if getattr(user_cT, col) != getattr(user_TDB, col):
                            if verbose:
                                r += "\n---- Colonne différant : {} (TDB : {}, cache_TDB : {})".format(col, getattr(user_TDB, col), getattr(user_cT, col))
                                
                            setattr(user_cT, col, getattr(user_TDB, col))
                            flag_modified(user_cT, col)
                            # Modifs.append( ( id, col, str(getattr(user_TDB, col))+"_EAT" ) )
                            Modifs.append( ( id, col, getattr(user_TDB, col) ) )        # Avec le passage direct à Chatfuel, plus besoin de _EAT. La modif ne sera indiquée dans le TDB que si tout est successful.
                            if id not in Modified_ids:
                                Modified_ids.append(id)
                                


            ### MODIFICATIONS DANS CHATFUEL DIRECT (WIP)
            
            if Modified_ids != []:
                BOT_ID = "5be9b3b70ecd9f4c8cab45e0"
                CHATFUEL_TOKEN = "mELtlMAHYqR0BvgEiMq8zVek3uYUK3OJMbtyrdNPTrQB9ndV0fM7lWTFZbM4MZvD"
                CHATFUEL_TAG = "CONFIRMED_EVENT_UPDATE"
                
                params_r = {"chatfuel_token" : CHATFUEL_TOKEN,
                            "chatfuel_message_tag" : CHATFUEL_TAG,
                            "chatfuel_block_name" : "Sync"}
                        
                for id in Modified_ids:
                    
                    # if id == 2033317286706583:      # PROVISOIRE : ne trigger que sur moi
                    
                    attrs = {}
                    for (idM, col, v) in Modifs:
                        if id == idM:
                            attrs[col] = v
                            attrs["sync_{}".format(col)] = True
                            
                    params = format_Chatfuel(attrs)
                    for k,v in params_r.items():
                        params[k] = v
                        
                    url_params = "&".join(["{}={}".format(k,v) for k,v in params.items()])
                    
                    rep = requests.post("https://api.chatfuel.com/bots/{}/users/{}/send?{}".format(BOT_ID, id, url_params))
                    rep = rep.json()
                    
                    if "code" in rep:
                        raise Exception("Erreur d'envoi Chatfuel Broadcast API. Réessaie.")
                    else:
                        if not rep["success"]:
                            raise Exception("Chatfuel Broadcast API a renvoyé une erreur : {}".format(rep["result"]))


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
                # raise KeyError("{}/{}".format(lm,cm))
                # a = ""
                cells_to_update = []
                for (l, c, v) in Modifs_rdy:
                    cell = [cell for cell in filter(lambda cell:cell.col == c+1 and cell.row == l+1, cells)][0]
                    cell.value = v       # cells : ([<L1C1>, <L1C2>, ..., <L1Ccm>, <L2C1>, <L2C2>, ..., <LlmCcm>]
                    cells_to_update.append(cell)
                    # a += "lm:{}/cm:{} - l:{}/c:{} - .row:{}/.col:{}\n".format(lm, cm, l, c, cell.row, cell.col)
                    
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
        return (400, "{}({})".format(type(e).__name__, str(e)))     # Affiche le "traceback" (infos d'erreur Python) en cas d'erreur (plutôt qu'un 501 Internal Server Error)
        # return (400, "".join(traceback.format_exc()))     # Affiche le "traceback" (infos d'erreur Python) en cas d'erreur (plutôt qu'un 501 Internal Server Error) 
        
    else:
        return r



### sync_Chatfuel

def sync_Chatfuel(d, j):    # d : pseudo-dictionnaire des arguments passés en GET (pwd) ; j : dictionnaire équivalent à la requête JSON de Chatfuel
    R = []  # Liste des blocs envoyés en réponse
    try:
        if ("pwd" in d) and (d["pwd"] == GLOBAL_PASSWORD):      # Vérification mot de passe
            
            ### GÉNÉRALITÉS
            
            cols = [str(column.key) for column in cache_Chatfuel.__table__.columns]      # Colonnes de cache_Chatfuel
            cols_SQL_types = {col:type(getattr(cache_Chatfuel, col).property.columns[0].type).__name__ for col in cols}
            cols_SQL_nullable = {col:getattr(cache_Chatfuel, col).property.columns[0].nullable for col in cols}
            
            # verbose = ( ("role" in j) and j["role"] == "MJ" )     # verbose auto pour les MJ
            verbose = ('v' in d)
            if verbose:
                R.append(chatfuel.Text("Mise à jour en cours (mode verbose activé)"))
                
                
            ### CONVERSION INFOS CHATFUEL EN UTILISATEURS
            
            joueur = {col:transtype(j[col], col, cols_SQL_types[col], cols_SQL_nullable[col]) for col in cols}
            user_Chatfuel = cache_Chatfuel(**joueur)
            id = user_Chatfuel.messenger_user_id
            
            
            ### RÉCUPÉRATION UTILISATEURS CACHES
            
            users_cC = cache_Chatfuel.query.all()     # Liste des joueurs tels qu'actuellement en cache côté Chatfuel
            ids_cC = [user_cC.messenger_user_id for user_cC in users_cC]
            
            users_cT = cache_TDB.query.all()          # Liste des joueurs tels qu'actuellement en cache côté TDB
            ids_cT = [user_cT.messenger_user_id for user_cT in users_cT]
            
            
            ### COMPARAISON
            
            Modifs_TDB = []         # Modifs à porter au TDB : tuple (id - colonne (nom) - valeur)
            Modifs_Chatfuel = {}    # Arguments à mettre à jour
            
            if (id not in ids_cC) or (id not in ids_cT):        # Joueur non enregistré
                R.extend([chatfuel.Text("⚠ Tu n'es pas inscrit dans nos fichiers ! ⚠"),
                            chatfuel.Buttons("Si tu viens d'arriver, c'est normal. Sinon, appelle un MJ !",
                                            [chatfuel.Button("show_block", "🆘 MJ ALED 🆘", "MJ ALED"),
                                            chatfuel.Button("show_block", "🏠 Retour menu", "Menu")])
                        ])
            else:
                if verbose:
                    R.append(chatfuel.Text("IDs existants."))

                user_cC = [user for user in users_cC if user.messenger_user_id==id][0]    # user correspondant dans cache_Chatfuel
                user_cT = [user for user in users_cT if user.messenger_user_id==id][0]    # user correspondant dans cache_TDB
                
                # Comparaison Chatfuel et cache_Chatfuel. En théorie, il ne devrait jamais y avoir de différence, sauf si quelqu'un s'amuse à modifier un attribut direct dans Chatfuel – ce qu'il ne faut PAS (plus) faire, parce qu'on ré-écrase
                
                if user_cC != user_Chatfuel:
                    for col in cols:
                        if getattr(user_cC, col) != getattr(user_Chatfuel, col):
                            if verbose:
                                R.append(chatfuel.Text("Différence ENTRE CACHE_CHATFUEL ET CHATFUEL détectée : {} (cache_Chatfuel : {}, Chatfuel : {})".format(col, getattr(user_cC, col), getattr(user_Chatfuel, col))))

                            # On écrase : c'est cache_Chatfuel qui a raison
                            Modifs_Chatfuel[col] = getattr(user_cC, col)
                                
                # Comparaison des caches. C'est là que les modifs apportées au TDB (et synchronisées) sont repérées
                
                if user_cC != user_cT:
                    for col in cols:
                        if getattr(user_cC, col) != getattr(user_cT, col):  # Si différence :
                            
                            if verbose:
                                R.append(chatfuel.Text("Différence détectée : {} (TDB : {}, Chatfuel : {})".format(col, getattr(user_cT, col), getattr(user_cC, col))))
                                
                            # On cale cache_Chatfuel sur cache_TDB :
                            setattr(user_cC, col, getattr(user_cT, col))
                            flag_modified(user_cC, col)
                            
                            # On modifie le TDB pour informer que la MAJ a été effectuée
                            Modifs_TDB.append( ( id, col, getattr(user_cT, col) ) )
                            
                            # On modifie l'attribut dans Chatfuel
                            Modifs_Chatfuel[col] = getattr(user_cT, col)
                            
                            
            ### COMMENTAIRE DES MODIFICATIONS CHATFUEL (INFORMATION JOUEUR)
            # L'application des modifications (changement des attributs) se fait directement à l'envoi de la réponse, à la toute fin de cette fonction.
            
            if Modifs_Chatfuel != {}:
                if len(Modifs_Chatfuel) > 8:
                    raise ValueError("Chatfuel ne peut pas envoyer plus de 10 messages ! Dis aux MJs de se calmer un peu !")
                    
                R.append(chatfuel.Text("⚡ Une action divine vient d'apporter quelques modifications à ton existance :"))
                for col in cols:
                    if col in Modifs_Chatfuel:
                        attr = Modifs_Chatfuel[col]
                        
                        if col == "inscrit":
                            if attr:
                                r = "Tu es maintenant considéré(e) comme participant au jeu."
                            else:
                                r = "Tu n'es maintenant plus considéré(e) comme participant au jeu."
                        elif col == "nom":
                            r = "Tu t'appelles maintenant {}.".format(attr)
                        elif col == "chambre":
                            r = "Tu est maintenant domicilié(e) en {}.".format(attr)
                        elif col == "statut":
                            if attr == "mort":
                                r = "Tu est malheureusement décédé(e) 😥\nÇa arrive même aux meilleurs, en espérant que ta mort ait été belle !"
                            elif attr == "MV":
                                r = "Te voilà maintenant réduit(e) au statut de mort-vivant... Un MJ viendra te voir très vite, si ce n'est déjà fait, mais la partie n'est pas finie pour toi !"
                            elif attr == "vivant":
                                r = "Tu es maintenant en vie. EN VIE !!!!"
                            else:
                                r = "Nouveau statut : {}".format(attr)
                        elif col == "role":
                            r = "Ton nouveau rôle, si tu l'acceptes : {} !\nQue ce soit pour un jour ou pour le reste de la partie, renseigne toi en écrivant « {} » en texte libre.".format(attr, attr)
                        elif col == "camp":                                 # IL FAUDRAIT ICI séparer selon les camps pour un message perso (flemme)
                            r = "Tu fais maintenant partie du camp « {} ».".format(attr)
                        elif col == "votantVillage":
                            if attr:
                                r = "Tu peux maintenant participer aux votes du village !"
                            else:
                                r = "Tu ne peux maintenant plus participer aux votes du village."
                        elif col == "votantLoups":
                            if attr:
                                r = "Tu peux maintenant participer aux votes des loups ! Amuse-toi bien 🐺"
                            else:
                                r = "Tu ne peux maintenant plus participer aux votes des loups."
                        elif col == "roleActif":
                            if attr:
                                r = "Tu peux maintenant utiliser le pouvoir associé à ton rôle !"
                            else:
                                r = "Tu ne peux maintenant plus utiliser le pouvoir associé à ton rôle."
                        elif col == "debutRole":
                            if attr == None:
                                r = "Tu n'as plus d'horaire de début de rôle..."
                            else:
                                r = "Nouveaux horaires ! ⏰\nTu peux maintenant utiliser ton action de rôle à partir de {}h...".format(attr)
                        elif col == "finRole":
                            if attr == None:
                                r = "... ni de fin de rôle."
                            else:
                                r = "... et avant {}h.".format(attr)
                                
                                
                        R.append(chatfuel.Text(" - " + r))
                        
                R.append(chatfuel.Buttons("⚠ Si tu penses qu'il y a erreur, appelle un MJ au plus vite ! ⚠",
                                            [chatfuel.Button("show_block", "Retour menu 🏠", "Menu"),
                                            chatfuel.Button("show_block", "MJ ALED 🆘", "MJ ALED")
                                            ]))
                                            
            
            ### APPLICATION DES MODIFICATIONS SUR LE TDB
            # Bon, il faut se connecter à GSheets, récupérer les IDs, tout ça... C'est un peu long du coup on le fait que si Modifs_TDB est vide
            
            if Modifs_TDB != []:
                Modifs_rdy = []
                lm = 0
                cm = 0
                
                workbook = gsheets.connect("1D5AWRmdGRWzzZU9S665U7jgx7U5LwvaxkD8lKQeLiFs")  # [DEV NextStep]
                sheet = workbook.worksheet("Journée en cours")
                values = sheet.get_all_values()     # Liste de liste des valeurs
                (NL, NC) = (len(values), len(values[0]))

                head = values[2]
                TDB_tampon_index = {col:head.index("tampon_"+col) for col in cols if col != 'messenger_user_id'}    # Dictionnaire des indices des colonnes GSheet pour chaque colonne de la partie « tampon »
                
                rows_TDB = {}               # Indices des lignes ou sont les différents joueurs du TDB
                
                for l in range(NL):
                    L = values[l]
                    id = L[head.index('messenger_user_id')]
                    if (id != "") and RepresentsInt(id):
                        rows_TDB[int(id)] = l
                        
                for (id, col, v) in Modifs_TDB:     # Modification de la partie « tampon » du TDB
                    l = rows_TDB[id]                # gspread indexe à partir de 1 (comme les gsheets, mais bon...)
                    if l > lm:
                        lm = l
                    c = TDB_tampon_index[col]
                    if c > cm:
                        cm = c
                    if v == None:
                        v = '' 
                    elif v == "None_EAT":
                        v = "_EAT"
                    Modifs_rdy.append((l, c, v))
                    
                # Récupère toutes les valeurs sous forme de cellules gspread
                cells = sheet.range(1, 1, lm+1, cm+1)   # gspread indexe à partir de 1 (comme les gsheets)
                
                cells_to_update = []
                for (l, c, v) in Modifs_rdy:
                    cell = [cell for cell in filter(lambda cell:cell.col == c+1 and cell.row == l+1, cells)][0]
                    cell.value = v       # cells : ([<L1C1>, <L1C2>, ..., <L1Ccm>, <L2C1>, <L2C2>, ..., <LlmCcm>]
                    cells_to_update.append(cell)
                    
                sheet.update_cells(cells_to_update)
                    
                
            ### APPLICATION DES MODIFICATIONS SUR LES BDD cache
            
            db.session.commit()     # Modification de cache_TDB
            
            
            ### FIN DE LA PROCÉDURE
                
            if verbose:
                R.append(chatfuel.Text("Fin de la procédure."))
                
        else:
            raise ValueError("WRONG OR MISSING PASSWORD!")
            
    except Exception as exc:
        db.session.rollback()
        if type(exc).__name__ == "OperationalError":
            return chatfuel.ErrorReport(Exception("Impossible d'accéder à la BDD, réessaie ! (souvent temporaire)"), verbose=verbose, message="Une erreur technique est survenue 😪\n Erreur :")
        else:
            return chatfuel.ErrorReport(exc, verbose=verbose, message="Une erreur technique est survenue 😪\nMerci d'en informer les MJs ! Erreur :")
    else:
        return chatfuel.Response(R, set_attributes=(format_Chatfuel(Modifs_Chatfuel) or None))



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
                R.append(chatfuel.Text("Liste des {}/{} joueurs {} :".format(NR, NT, descr)))
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
        r = "<h1>« Panneau d'administration » (vaguement, hein) LG Rez</h1><hr/>".format(dict(d), dict(p))

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
                
                user_cT = cache_TDB.query.filter_by(messenger_user_id=44444444).first()
                user_cT.nom = "BONSOIR"
                db.session.commit()
            
            if "oskour" in d:
                r += "OSKOUR<br/>"
                db.session.rollback()
                r += "OSKOUUUUR<br/>"
            

            ### CHOIX D'UNE OPTION
                
            r += """<hr/><br />
                    <form action="admin?pwd={}" method="post">
                        <div>
                            <fieldset>
                                <legend>Voir une table</legend>
                                Table : 
                                <label for="cache_TDB">cache_TDB </label> <input type="radio" name="table" value="cache_TDB" id="cache_TDB"> / 
                                <label for="cache_Chatfuel">cache_Chatfuel </label> <input type="radio" name="table" value="cache_Chatfuel" id="cache_Chatfuel">
                                <input type="submit" name="viewtable", value="Voir la table">
                            </fieldset>
                        </div>
                    </form>
            """.format(GLOBAL_PASSWORD)


            ### ARGUMENTS BRUTS (pour débug)
            
            r += """<br/><hr/><br/>
                <div>
                    <i>
                        GET args:{} <br/>
                        POST args:{}
                    </i>
                </div>""".format(dict(d), dict(p))

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
                    
            r += "Requête : <pre>{}</pre>".format(json.dumps(params, indent=4))
            
            url_params = "&".join(["{}={}".format(k,v) for k,v in params.items()])
            
            rep = requests.post("https://api.chatfuel.com/bots/{}/users/{}/send?{}".format(BOT_ID, id, url_params))
            r += "<br /><br />Réponse : <pre>{}</pre>".format(rep.text)

        else:
            raise ValueError("WRONG OR MISSING PASSWORD!")

    except Exception:
        r += infos_tb()     # Affiche le "traceback" (infos d'erreur Python) en cas d'erreur (plutôt qu'un 501 Internal Server Error)

    finally:
        return r
