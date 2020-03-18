from __init__ import db, cache_TDB, cache_Chatfuel
from sqlalchemy.exc import *        # Exceptions générales SQLAlchemy
from sqlalchemy.orm.exc import *    # Exceptions requêtes SQLAlchemy
from sqlalchemy.orm.attributes import flag_modified
from flask import abort

import blocs.chatfuel as chatfuel
import blocs.gsheets as gsheets
import string, random
import sys, traceback


GLOBAL_PASSWORD = "C'estSuperSecure!"


### UTILITAIRES

def strhtml(r):
    return r.replace('\n', '<br/>')

def infos_tb(quiet=False):
    tb = "".join(traceback.format_exc()).replace('&','&esp;').\
                                         replace('<','&lt;').\
                                         replace('>','&gt;')
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

def transtype(value, col, SQL_type, nullable):      # Utilitaire : type un input brut (POST, GET...) selon le type de sa colonne
    try:
        if value in (None, '', 'None', 'none', 'Null', 'null'):
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
            
            workbook = gsheets.connect("1D5AWRmdGRWzzZU9S665U7jgx7U5LwvaxkD8lKQeLiFs")  # [DEV NextStep]
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
                    user = cache_TDB(**joueur)
                    
                    users_TDB.append(user)
                    ids_TDB.append(user.messenger_user_id)
                    rows_TDB[user.messenger_user_id] = l
                    
                    
            ### RÉCUPÉRATION UTILISATEURS CACHE
            
            users_cache = cache_TDB.query.all()     # Liste des joueurs tels qu'actuellement en cache
            ids_cache = [user.messenger_user_id for user in users_cache]
                    
                
            ### COMPARAISON
            
            Modifs = []         # Modifs à porter au TDB : tuple (id - colonne (nom) - valeur)
            
            for user in users_cache.copy():                      ## 1. Joueurs dans le cache supprimés du TDB
                if user.messenger_user_id not in ids_TDB:
                    users_cache.remove(user)
                    db.session.delete(user)
                    if verbose:
                        r += "\nJoueur dans le cache hors TDB : {}".format(user)
                    
            for user in users_TDB:                               ## 2. Joueurs dans le TDB pas encore dans le cache
                if user.messenger_user_id not in ids_cache:
                    users_cache.append(user)
                    db.session.add(user)
                    id = user.messenger_user_id
                    if verbose:
                        r += "\nJoueur dans le TDB hors cache : {}".format(user)
                    
                    Modifs.extend( [( id, col, str(getattr(user, col))+"_EAT" ) for col in cols if col != 'messenger_user_id'] )
                    
            # À ce stade, on a les même utilisateurs dans users_TDB et users_cache (mais pas forcément les mêmes infos !)
            
            for user_TDB in users_TDB:                           ## 3. Différences
                user_cache = [user for user in users_cache if user.messenger_user_id==user_TDB.messenger_user_id][0]    # user correspondant dans le cache
                    
                if user_cache != user_TDB:     # Au moins une différence !
                    if verbose:
                        r += "\nJoueur différant entre TDB et cache : {}".format(user_TDB)
                    id = user_TDB.messenger_user_id
                    
                    for col in cols:
                        if getattr(user_cache, col) != getattr(user_TDB, col):
                            setattr(user_cache, col, getattr(user_TDB, col))
                            flag_modified(user_cache, col)
                            Modifs.append( ( id, col, str(getattr(user_TDB, col))+"_EAT" ) )
                            if verbose:
                                r += "\n---- Colonne différant : {} (TDB : {}, cache : {})".format(col, getattr(user_TDB, col), getattr(user_cache, col))
                                
                                
            ### APPLICATION DES MODIFICATIONS
            
            cells_to_update = []
            for (id, col, v) in Modifs:     # Modification de la partie « tampon » du TDB
                l = rows_TDB[id] + 1                # gspread indexe à partir de 1 (comme les gsheets, mais bon...)
                c = TDB_tampon_index[col] + 1
                
                cell = sheet.cell(l, c)
                cell.value = v
                cells_to_update.append(cell)
                
            if cells_to_update != []:
                sheet.update_cells(cells_to_update)
                
                if verbose:
                    r += "\n\n" + "\n".join([str(m) for m in Modifs])
                
            db.session.commit()     # Modification de cache_TDB
            
            ### FIN DE LA PROCÉDURE
            
        else:
            raise ValueError("WRONG OR MISSING PASSWORD!")
            
    except Exception as e:
        db.session.expunge_all()
        return (400, "{}({})".format(type(e).__name__, str(e)))     # Affiche le "traceback" (infos d'erreur Python) en cas d'erreur (plutôt qu'un 501 Internal Server Error)
        
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
            
            verbose = ( ("role" in j) and j["role"] == "MJ" )
            if verbose:
                R.append(chatfuel.Text("Mise à jour en cours (mode verbose activé)"))
                
                
            ### CONVERSION INFOS CHATFUEL EN UTILISATEURS
            
            joueur = {col:transtype(j[col], col, cols_SQL_types[col], cols_SQL_nullable[col]) for col in cols}
            user_Chatfuel = cache_Chatfuel(**joueur)
            id = user_Chatfuel.messenger_user_id
            
            # db.session.add(user)
            # db.session.commit()
            
            
            ### RÉCUPÉRATION UTILISATEURS CACHES
            
            users_cC = cache_Chatfuel.query.all()     # Liste des joueurs tels qu'actuellement en cache
            ids_cC = [user.messenger_user_id for user in users_cC]
            
            users_cT = cache_TDB.query.all()          # Liste des joueurs tels qu'actuellement en cache
            ids_cT = [user.messenger_user_id for user in users_cT]
            
            
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
                    
                if user_cC != user_Chatfuel:     # Comparaison Chatfuel et cache_Chatfuel. En théorie, il ne devrait jamais y avoir de différence, sauf si quelqu'un s'amuse à modifier un attribut direct dans Chatfuel – ce qu'il ne faut PAS (plus) faire, parce qu'on ré-écrase
                    for col in cols:
                        if getattr(user_cC, col) != getattr(user_Chatfuel, col):
                            # On écrase : c'est cache qui a raison
                            Modifs_Chatfuel[col] = getattr(user_cC, col)
                            
                            if verbose:
                                R.append(chatfuel.Text("Différence ENTRE CACHE_CHATFUEL ET CHATFUEL détectée : {} (cache : {}, Chatfuel : {})".format(col, getattr(user_cC, col), getattr(user_Chatfuel, col))))
                                
                                
                if user_cC != user_cT:          # Comparaison des caches. C'est là que les modifs apportées au TDB (et synchronisées) sont repérées.
                    for col in cols:
                        if getattr(user_cC, col) != getattr(user_cT, col):  # Si différence :
                            
                            # On cale cache_Chatfuel sur cache_TDB :
                            setattr(user_cC, col, getattr(user_cT, col))
                            flag_modified(user_cC, col)
                            
                            # On modifie le TDB pour informer que la MAJ a été effectuée
                            Modifs_TDB.append( ( id, col, str(getattr(user_cT, col)) ) )
                            
                            # On modifie l'attribut dans Chatfuel
                            Modifs_Chatfuel[col] = getattr(user_cT, col)
                            
                            if verbose:
                                R.append(chatfuel.Text("Différence détectée : {} (TDB : {}, Chatfuel : {})".format(col, getattr(user_cT, col), getattr(user_cC, col))))
                                
            ### FIN DE LA PROCÉDURE
                
            if verbose:
                R.append(chatfuel.Text("Fin de la procédure."))
                
        else:
            raise ValueError("WRONG OR MISSING PASSWORD!")
            
    except Exception as exc:
        db.session.expunge_all()
        return chatfuel.ErrorReport(exc, verbose=verbose, message="Une erreur est survenue. Merci d'en informer les MJs !")
        
    else:
        return chatfuel.Response(R)



    

### OPTIONS DU PANNEAU D'ADMIN

exec(open("./blocs/admin_options.py").read())



def getsetcell(d):
    r = ""
    try:
        if ("pwd" in d) and (d["pwd"] == GLOBAL_PASSWORD):

            key = "1D5AWRmdGRWzzZU9S665U7jgx7U5LwvaxkD8lKQeLiFs" if 'k' not in d else d['k']

            workbook = gsheets.connect(key)
            r += "Classeur : {}\n".format(workbook.title)

            s = 0 if 's' not in d else int(d['s'])

            sheet = workbook.get_worksheet(s)
            r += "Feuille n°{} ({})\n".format(s, sheet.title)

            if 'a' in d:
                a = d['a']
                c = sheet.acell(a)
                r += "Cellule {} :\n\n".format(a)
            else:
                row = 12 if 'r' not in d else int(d['row'])
                col = 10 if 'c' not in d else int(d['col'])
                c = sheet.cell(row,col)
                r += "Ligne {}, colonne {} :\n\n".format(row,col)

            r += c.value

            if 'nv' in d:
                c.value = d['nv']
                sheet.update_cells([c])

        else:
            raise ValueError("WRONG OR MISSING PASSWORD!")
    except Exception as exc:
        r += "\n\n AN EXCEPTION HAS BEEN RAISED!\n"
        r += "{}: {}".format(type(exc).__name__,exc)
    finally:
        return r.replace('\n','<br/>')


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
                
            
            if "testupdate" in d:
                
                r += "<br/>TEST UPDATE 44444444<br/>"
                
                user = cache_TDB.query.filter_by(messenger_user_id=44444444).first()
                user.nom = "BONSOIR"
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
        user_TDB = cache_TDB(messenger_user_id = random.randrange(1000000000),
                            inscrit = True,
                            nom = d["a_creer"],
                            chambre = random.randrange(101,800),
                            statut = "test",
                            role = "rôle"+str(random.randrange(15)),
                            camp = "camp"+str(random.randrange(3)),
                            votantVillage = random.randrange(1),
                            votantLoups = random.randrange(1))

        db.session.add(user_TDB)
        db.session.commit()

        cont = [e.nom for e in cache_TDB.query.all()]

        rep= chatfuel.Response([    chatfuel.Text("Contenu de cache_TDB (2) :"),
                                    chatfuel.Text("\n".join(cont)),
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
