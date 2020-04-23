# Ce fichier est une partie de core.py, séparée pour plus de lisibilité. Il contient tous les « blocs » du panneau d'admin


### UTILITAIRES

def html_table(LL, first_row=None, row_start="", row_end=""):
    r = "<table style='border:1px solid black; border-collapse: collapse;'>"
    for L in [[f"<b>{e}</b>" for e in first_row]] + LL:
        r += f"<tr>{row_start}<td style='border:1px solid black; padding:2pt;'>"
        r += "</td><td style='border:1px solid black; padding:2pt;'>".join([str(l) for l in L])
        r += f"</td>{row_end}</tr>"
    r += "</table>"
    return r


### BASE DE DONNÉES

def viewtable(d, p):
    r = ""

    table = p["table"]
    r += f"<h2>Table : {table}</h2>"

    cols = [column.key for column in globals()[table].__table__.columns]
    LE = globals()[table].query.all()
    LE = [[ e.__dict__[k] for k in cols ] for e in LE]

    tete = [ee for ee in cols] + ["Action"]

    delButton = lambda x:f"""<form action="admin?pwd={GLOBAL_PASSWORD}" method="post"> <input type="hidden" name="table" value="{table}"> <input type="hidden" name="id" value="{x}"> <input type="submit" name="delitem" value="Suppr">"""

    corps = [e + [delButton(e[cols.index("messenger_user_id")])] for e in LE]

    itemDefault = {"messenger_user_id": random.randrange(1000000000),
                   "inscrit": True,
                   "nom": ''.join(random.choices(string.ascii_uppercase + string.digits + " ", k=6)),
                   "chambre": random.randrange(101,800),
                   "statut": "test",
                   "role": "rôle"+str(random.randrange(15)),
                   "camp": "camp"+str(random.randrange(3)),
                   "votantVillage": random.randrange(1),
                   "votantLoups": random.randrange(1),
                   "roleActif": None,
                   "debutRole": None,
                   "finRole": None,
                   }

    nouv = [f"""<input type="text" name="{ee}" size="10cm" value={itemDefault[ee]}>""" for ee in cols] + ["""<input type="submit" name="additem" value="Créer">"""]


    r += html_table(corps + [nouv],
                    tete,
                    f"""<form action="admin?pwd={GLOBAL_PASSWORD}" method="post">
                        <input type="hidden" name="table" value="{table}">""",
                    "</form>")
    r += "<br />"

    return r


def additem(d, p):
    r = ""

    table = p["table"]
    r += "<h2>Ajout d'élément</h2>"
    r += f"Table : {table}\n\n"

    user_TDB = globals()[table](
                        messenger_user_id = p["messenger_user_id"],
                        inscrit = bool(eval(p["inscrit"])),
                        nom = p["nom"],
                        chambre = p["chambre"],
                        statut = p["statut"],
                        role = p["role"],
                        camp = p["camp"],
                        votantVillage = bool(eval(p["votantVillage"])),
                        votantLoups = bool(eval(p["votantLoups"]))
                        )

    db.session.add(user_TDB)
    db.session.commit()

    r += "Ajout réussi.\n\n"

    return r


def delitem(d, p):
    r = ""

    table = p["table"]
    id = p["id"]
    r += "<h2>Suppression d'élément</h2>"
    r += f"Table : {table}, ID : {id}\n\n"

    try:
        user_TDB = globals()[table].query.filter_by(messenger_user_id=id).one()
        db.session.delete(user_TDB)
        db.session.commit()
        r += "Suppression effectuée.\n\n"
    except NoResultFound:
        r += "Aucun résultat trouvé. Suppression non effectuée.\n\n"
    except MultipleResultsFound:
        r += "Plusieurs résultats trouvés. Suppression non effectuée.\n\n"

    return r


### TÂCHES PLANIFIÉES

def viewcron(d, p):
    r = "<h2>Tâches planifiées alwaysdata</h2>"

    lst = getjobs()     # Récupération de la liste des tâches
    lst.sort(key=lambda x:x["id"])
    
    # for dic in lst[10:]:
    #     requests.patch(f'https://api.alwaysdata.com/v1/job/{dic["id"]}/', auth=(ALWAYSDATA_API_KEY, ''), json={'argument':dic['argument'].replace("\\!","")})
    #     time.sleep(0.1)

    keys = list(lst[0].keys())
    
    delButton = lambda id:f"""<input type="hidden" name="id" value="{id}"><input type="submit" name="delcron" value="Suppr">"""
    switchButton = lambda id,is_disabled:f"""<input type="hidden" name="id" value="{id}">{'' if is_disabled else '<input type="hidden" name="disable">'}<input type="submit" name="disablecron" value=" {'Activer' if is_disabled else 'Désactiver'}">"""
    
    corps = [[dic[k] for k in keys] + [delButton(dic["id"]) + switchButton(dic["id"], dic["is_disabled"])] for dic in lst]
    
    fieldProperties = {"id": None,
                       "href": None,
                       "type": ["TYPE_URLS", "TYPE_COMMAND"],
                       "date_type": ["DAILY", "FREQUENCY", "CRONTAB"],
                       "argument": f"https://lg-rez.alwaysdata.net/cron_call?pwd={GLOBAL_PASSWORD}&job=open_maire&heure=17",
                       "is_disabled": False,
                       "daily_time": f"{random.randrange(24):02}:{random.randrange(60):02}",
                       "frequency": "",
                       "frequency_period": ["", "minute", "hour", "day", "week", "month"],
                       "crontab_syntax": "",
                       }
                       
    def champ(k, arg):
        if arg is None:
            return "<i>readonly</i>"
        elif isinstance(arg, bool):
            return f"""<input type="checkbox" name="{k}" {"checked" if arg else ""}>"""
        elif isinstance(arg, str):
            return f"""<input type="text" name="{k}" size="{len(arg) if arg != "" else 10}" value="{arg}">"""
        elif isinstance(arg, int):
            return f"""<input type="number" name="{k}" value="{arg}">"""
        elif isinstance(arg, list):
            options = ''.join([f"""<option value="{a}">{a}</option>""" for a in arg])
            return f"""<select name="{k}">{options}</select>"""
        else:
            return "Unknow field property."
            
    nouv = [champ(k, fieldProperties[k]) for k in keys] + ["""<input type="submit" name="addcron" value="Créer">"""]
    
    r += html_table(corps + [nouv],
                    keys + ["Action"],
                    f"""<form action="admin?pwd={GLOBAL_PASSWORD}" method="post">""",
                    "</form>")
    
    return r


def addcron(d, p):
    r = "<h2>Ajout de tâche planifiée alwaysdata</h2>"
    
    dic = {"type": p["type"],
           "date_type": p["date_type"],
           "argument": p["argument"],
           "is_disabled": ("is_disabled" in p),
           "daily_time": p["daily_time"] or None,       # Syntaxe incroyable : si p["daily_time"] == "", évalué comme False ==> passe à None, sinon p["daily_time"]
           "frequency": p["frequency"] or None,
           "frequency_period": p["frequency_period"] or None,
           "crontab_syntax": p["crontab_syntax"] or None,
           }
           
    r += f"Requête : <pre>{dic}</pre><hr />"
           
    rep = requests.post('https://api.alwaysdata.com/v1/job/', auth=(f'{ALWAYSDATA_API_KEY} account=lg-rez', ''), json=dic)
    
    if rep:
        r += f"<pre>{rep.text}</pre><br />"
        r += "Ajout réussi.<hr />"
    else:
        raise ValueError(f"Request Error (HTTP code {rep.status_code})")
        
    return r


def delcron(d, p):
    r = "<h2>Suppression de tâche planifiée alwaysdata</h2>"
    
    id = p["id"]
    r += f"ID à supprimer : <code>{id}</code>"
           
    rep = requests.delete(f'https://api.alwaysdata.com/v1/job/{id}/', auth=(ALWAYSDATA_API_KEY, ''))
    
    if rep:
        r += f"<pre>{rep.text}</pre><br />"
        r += "Suppression réussie.<hr />"
    else:
        raise ValueError(f"Request Error (HTTP code {rep.status_code})")
        
    return r


def disablecron(d, p, id=False):
    r = "<h2>Désactivation/activation de tâche planifiée alwaysdata</h2>"
    
    if not id:
        id = p["id"]
    disable = ("disable" in p)
    
    r += f"ID : <code>{id}</code> / action : <code>{'disable' if disable else 'enable'}</code>"
           
    rep = requests.patch(f'https://api.alwaysdata.com/v1/job/{id}/', 
                         auth=(ALWAYSDATA_API_KEY, ''), 
                         json={"id":id, "is_disabled":disable})
    
    if rep:
        r += f"<pre>{rep.text}</pre>"
        r += f"{'Désactivation' if disable else 'Activation'} réussie.<hr />"
    else:
        raise ValueError(f"Request Error (HTTP code {rep.status_code})")
        
    return r


def sendjob(d, p):
    r = "<h2>Envoi de tâche</h2>"
    
    dic = {"pwd": d["pwd"],
           "job": p["job"],
           "heure": p["heure"] if "heure" in p else None,
           # "test": ("test" in p),
           "v": True,               # mode Verbose
           "return_tb": True,       # retourne le TB en cas d'exception
          }
          
    if "test" in p:
        dic["test"] = True
          
    r += cron_call(dic)
    
    return r + "<br/><br/>"
    
    
### AUTRES FONCTIONNALITÉS

def viewlogs(d, p):
    fich = f"{p['Y']:0>4}-{p['m']:0>2}-{p['d']:0>2}"
    
    r = f"<h2>Logs de cron_call – {fich}</h2>"
        
    try:
        with open(f"logs/cron_call/{fich}.log") as f:
            r += f"<pre>{html_escape(f.read())}</pre>"

    except FileNotFoundError:
        r += "Pas de log pour ce jour.<br/><br/>"
        
    return r


def restart_site(d, p):
    r = "<h2>Redémarrage du site</h2>"

    rep = requests.get('https://api.alwaysdata.com/v1/site/', auth=(ALWAYSDATA_API_KEY, ''), data={})
    if rep:
        # r += f"<pre>{rep.text}</pre><hr />"
        # r += f"<pre>{str(type(rep.json()))}</pre><hr />"
        try:
            site_id = rep.json()[0]["id"]
        except:
            site_id = 0
        # site_id = 594325
    else:
        raise ValueError(f"Request Error (HTTP code {rep.status_code})")
    
    rep = requests.post(f"https://api.alwaysdata.com/v1/site/{site_id}/restart/", auth=(ALWAYSDATA_API_KEY, ''))
    
    if rep:
        r += f"<pre>{rep.text}</pre>"
    else:
        raise ValueError(f"Request Error (HTTP code {rep.status_code})")
        
    return r


# STATUTS

def show_statuts(d, p):
    r = f"<br />{time.ctime()} – Statuts :"
    
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
            
    return r
