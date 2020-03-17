from __init__ import db, cache_TDB, cache_Chatfuel
from sqlalchemy.exc import *        # Exceptions générales SQLAlchemy
from sqlalchemy.orm.exc import *    # Exceptions requêtes SQLAlchemy
import blocs.chatfuel, blocs.gsheets
import string, random
import sys, traceback


GLOBAL_PASSWORD = "C'estSuperSecure!"


### UTILITAIRES

def strhtml(r):
    return r.replace('\n', '<br/>')

def infos_tb():
    tb = "".join(traceback.format_exc()).replace('&','&esp;').\
                                         replace('<','&lt;').\
                                         replace('>','&gt;')
    return "<br/><div> AN EXCEPTION HAS BEEN RAISED! <br/><pre>{}</pre></div>".format(tb)

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

### OPTIONS DU PANNEAU D'ADMIN

exec(open("./blocs/admin_options.py").read())

def sync_TDB(d):
    try:
        r = "sync_TDB:"
        
        if ("pwd" in d) and (d["pwd"] == GLOBAL_PASSWORD):      # Vérification mot de passe
        
            ### GÉNÉRALITÉS
            
            cols = [column.key for column in globals()["cache_TDB"].__table__.columns]      # Colonnes de cache_TDB
            
            cols_SQL_types = {col:type(cache_TDB.__dict__[col].property.columns[0].type).__name__ for col in cols}
            def transtype(value, col):      # Type un input brut (POST, GET...) selon le bon type
                if value == '':
                    return None
                elif cols_SQL_types[col] == "String":
                    return str(value)
                elif cols_SQL_types[col] in ("Integer", "BigInteger"):
                    return int(value)
                elif cols_SQL_types[col] == "Boolean":
                    return bool(value)
                else:
                    raise ValueError("unknown column type")
                    
                    
            ### RÉCUPÉRATION INFOS GSHEET
            
            workbook = blocs.gsheets.connect("1D5AWRmdGRWzzZU9S665U7jgx7U5LwvaxkD8lKQeLiFs")  # [DEV NextStep]
            sheet = workbook.worksheet("Journée en cours")
            values = sheet.get_all_values()     # Liste de liste des valeurs
            (NL, NC) = (len(values), len(values[0]))
            
            r += "<{}L/{}C>\n".format(NL, NC)
            
            head = values[2]
            TDB_index = {col:head.index(col) for col in cols}    # Dictionnaire des indices des colonnes GSheet pour chaque colonne de la table
                
            users_TDB = []              # Liste des joueurs tels qu'actuellement dans le TDB
            ids_TDB = []                # messenger_user_ids des différents joueurs du TDB
            rows_TDB = {}               # Indices des lignes ou sont les différents joueurs du TDB
            
            for l in range(NL):
                L = values[l]
                id = L[TDB_index["messenger_user_id"]]
                if (id != "") and RepresentsInt(id):
                    
                    joueur = {col:transtype(L[TDB_index[col]], col) for col in cols}
                    user = cache_TDB(**joueur)
                    
                    users_TDB.append(user)
                    ids_TDB.append(user.messenger_user_id)
                    rows_TDB[user.messenger_user_id] = l
                    
                    
            ### CHARGEMENT CACHE
            
            users_cache = cache_TDB.query.all()     # Liste des joueurs tels qu'actuellement en cache
            ids_cache = [user.messenger_user_id for user in users_cache]
                    
                
            ### COMPARAISON
                
            for user in users_cache:                            ## 1. Joueurs dans le cache supprimés du TDB
                if user.messenger_user_id not in ids_TDB:
                    users_cache.remove(user)
                    # db.session.delete(user)
                    r += "\nJoueur dans le cache hors TDB : {}".format(user)
                    
            for user in users_TDB:                               ## 2. Joueurs dans le TDB pas encore dans le cache
                if user.messenger_user_id not in ids_cache:
                    users_cache.append(user)
                    # db.session.add(user)
                    r += "\nJoueur dans le TDB hors cache : {}".format(user)
                    # Modif cache du TDB
                    
            # À ce stade, on a les même utilisateurs dans users_TDB et users_cache (mais pas forcément les mêmes infos !)
                
            for user_TDB in users_TDB:
                user_cache = [user for user in users_cache if user.messenger_user_id==user_TDB.messenger_user_id][0]
                
                if user_cache != user_TDB:     # Au moins une différence !
                    r += "\nJoueur différant entre TDB et cache : {}".format(user_TDB)
                    for col in cols:
                        if user_cache.__dict__[col] != user_TDB.__dict__[col]:
                            r += "\n---- Colonne différant : {} (TDB : {}, cache : {})".format(col, user_TDB.__dict__[col], user_cache.__dict__[col])
                                
            
        else:
            raise ValueError("WRONG OR MISSING PASSWORD!")
            
    except Exception:
        r += infos_tb()     # Affiche le "traceback" (infos d'erreur Python) en cas d'erreur (plutôt qu'un 501 Internal Server Error)
        
    finally:
        return r



def getsetcell(d, p):
    r = ""
    try:
        if ("pwd" in d) and (d["pwd"] == GLOBAL_PASSWORD):

            workbook = gsheets.connect()
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
                
                cols = [column.key for column in cache_TDB.__table__.columns]
                user = cache_TDB.query.filter_by(messenger_user_id=44444444).first()
                user.nom = "BONSOIR"
                db.session.commit()
                


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
