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


### OPTIONS DU PANNEAU D'ADMIN

exec(open("./blocs/admin_options.py").read())

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
