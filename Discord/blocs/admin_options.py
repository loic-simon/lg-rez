# Ce fichier est une partie de core.py, séparée pour plus de lisibilité. Il contient tous les « blocs » du panneau d'admin


### UTILITAIRES

def html_table(LL, first_row=None, second_row=None, last_row=None, repeat_header=False, very_last_row=None, row_start="", row_end=""):
    r = "<table style='border:1px solid black; border-collapse: collapse;'>"
    if second_row:
        LL.insert(0, [f"<i>{e}</i>" for e in second_row])
    if first_row:
        LL.insert(0, [f"<b>{e}</b>" for e in first_row])
    if last_row:
        LL.append([f"<b>{e}</b>" for e in last_row])
    if repeat_header:
        LL.append([f"<b>{e}</b>" for e in first_row])
    if very_last_row:
        LL.append(very_last_row)
    for L in LL:
        r += f"<tr>{row_start}<td style='border:1px solid black; padding:2pt;'><nobr>"
        r += "</nobr></td><td style='border:1px solid black; padding:2pt;'><nobr>".join([str(l) for l in L])
        r += f"</nobr></td>{row_end}</tr>"
    r += "</table>"
    return r


### BASE DE DONNÉES

def viewtable(d, p, sort_col=None, sort_asc=None):
    r = ""

    table = Tables[p["table"]]
    r += f"<h2>Table : {table.__name__}</h2>"

    cols = bdd_tools.get_cols(table)
    primary_col = bdd_tools.get_primary_col(table)
    SQL_type = bdd_tools.get_SQL_types(table, detail=True)
    SQL_nullable = {col:val if type(SQL_type[col]).__name__ != "Boolean" else True for (col, val) in bdd_tools.get_SQL_nullable(table).items()}

    def HTMLform_type(SQL_type):
        SQL_type_name = type(SQL_type).__name__
        map_types = {"String": "text",
                     "Text": "text",
                     "Integer": "number",
                     "BigInteger": "number",
                     "Boolean": "checkbox",
                     "Time": "time",
                     }
        try:
            return map_types[SQL_type_name]
        except KeyError:
            raise KeyError(f"unknown column type: '{SQL_type_name}''")

    def HTMLform_value(SQL_type, value):
        SQL_type_name = type(SQL_type).__name__
        maxcar = int(str(SQL_type)[8:-1]) if SQL_type_name == 'String' else 0
        map_values = {"String": f"""{f'value="{value}"' if value else ""} size=\"{min(0.4*maxcar, 60)}cm" """,
                      "Text": f"""{f'value="{value}"' if value else ""} size="20cm" """,
                      "Integer": f"""{f'value={value}' if value is not None else ""} style="width:1.5cm" """,
                      "BigInteger": f"""{f'value={value}' if value is not None else ""} style="width:4cm" """,
                      "Boolean": "checked" if str(value).lower() == "true" else "",
                      "Time": f"value={value}" if value else "",
                      }
        try:
            return map_values[SQL_type_name]
        except KeyError:
            raise KeyError(f"unknown column type: '{SQL_type_name}''")

    if sort_col:
        if sort_asc:
            LE = table.query.order_by(getattr(table, sort_col)).all()
        else:
            LE = table.query.order_by(getattr(table, sort_col).desc()).all()
    else:
        LE = table.query.all()
    LE = [{col:getattr(e, col) for col in cols} for e in LE]

    def boutons(value):
        return (f"""<input type="submit" name="editem" value="Édit">"""
                f"""<input type="submit" name="delitem" value="Suppr">""")

    corps = [[f"""<input type=\"{HTMLform_type(SQL_type[col])}" name=\"{col}" {HTMLform_value(SQL_type[col], val)} {"readonly" if col == primary_col or col.startswith("_") else ""} {"" if SQL_nullable[col] else "required"}>""" for (col, val) in d.items()] + [boutons(d[primary_col])] for d in LE]

    nouv = [f"""<input type=\"{HTMLform_type(SQL_type[col])}" name=\"{col}" {HTMLform_value(SQL_type[col], None)} {"disabled" if col.startswith("_") else ""} {"" if SQL_nullable[col] else "required"}>""" for col in cols] + ["""<input type="submit" name="additem" value="Créer">"""]

    def actual_sort(col, asc):
        return """disabled style="background-color:yellow;" """ if col == sort_col and asc == sort_asc else ""
    first_row = [(f"""{col}<br/><input type=submit name="viewtable-sort:{col}:asc" value="&and;" {actual_sort(col, True)}>"""
                  f"""<input type=submit name="viewtable-sort:{col}:desc" value="&or;" {actual_sort(col, False)}>""") for col in cols] + ["""Action <input type=submit name="viewtable" value="&times;">"""]

    r += html_table(corps,
                    # first_row = cols + ["Action"],
                    first_row = first_row,
                    second_row = [f"""{SQL_type[col]}{"" if SQL_nullable[col] else "*"}""" for col in cols] + [""],
                    repeat_header = True,
                    very_last_row = nouv,
                    row_start = (f"""<form action="admin?pwd={GLOBAL_PASSWORD}" method="post">"""
                                 f"""<input type="hidden" name="table" value=\"{table.__name__}">"""
                                 f"""<input type="hidden" name="primary_col" value=\"{primary_col}">"""),
                    row_end = "</form>")
    r += "<br />"

    return r


def additem(d, p):
    r = "<h2>Ajout d'élément</h2>"

    table = Tables[p["table"]]
    r += f"Table : {table.__name__}\n\n"
    
    cols = [col for col in bdd_tools.get_cols(table) if not col.startswith("_")]
    SQL_type = bdd_tools.get_SQL_types(table)
    SQL_nullable = bdd_tools.get_SQL_nullable(table)

    args = {col:bdd_tools.transtype(p[col] if col in p else False, col, SQL_type[col], SQL_nullable[col]) for col in cols}

    user = table(**args)
    db.session.add(user)
    db.session.commit()

    r += "Ajout réussi.\n\n"
    return r


def delitem(d, p):
    r = "<h2>Suppression d'élément</h2>"

    table = Tables[p["table"]]
    id = {p["primary_col"]:p[p["primary_col"]]}
    r += f"Table : {table.__name__}, ID : {id}<br/><br/>"

    try:
        user = table.query.filter_by(**id).one()
        db.session.delete(user)
        db.session.commit()
        r += "Suppression effectuée.<br/><br/>"
    except NoResultFound:
        r += "Aucun résultat trouvé. Suppression non effectuée.<br/><br/>"
    except MultipleResultsFound:
        r += "Plusieurs résultats trouvés. Suppression non effectuée.<br/><br/>"

    return r


def editem(d, p):
    r = "<h2>Modification d'élément</h2>"

    table = Tables[p["table"]]
    id = {p["primary_col"]:p[p["primary_col"]]}
    r += f"Table : {table.__name__}, ID : {id}<br/><ul>"
    
    cols = [col for col in bdd_tools.get_cols(table) if not col.startswith("_")]
    SQL_type = bdd_tools.get_SQL_types(table)
    SQL_nullable = bdd_tools.get_SQL_nullable(table)

    args = {col:bdd_tools.transtype(p[col] if col in p else False, col, SQL_type[col], SQL_nullable[col]) for col in cols}

    try:
        user = table.query.filter_by(**id).one()
        for col in cols:
            if (old := getattr(user, col)) != (new := args[col]):
                r += f"<li>{col} : {old} &rarr; {new}</li>"
                bdd_tools.modif(user, col, new)
        r += "</ul>"
        db.session.commit()
        r += "Modification effectuée.<br/><br/>"
    except NoResultFound:
        r += "Aucun résultat trouvé. Modification non effectuée.<br/><br/>"
    except MultipleResultsFound:
        r += "Plusieurs résultats trouvés. Modification non effectuée.<br/><br/>"

    return r


### TÂCHES PLANIFIÉES

def viewcron(d, p):
    r = "<h2>Tâches planifiées alwaysdata</h2>"

    lst = getjobs()     # Récupération de la liste des tâches
    lst.sort(key=lambda x:x["id"])

    keys = list(lst[0].keys())

    def boutons(id, is_disabled):
        return (f"""<input type="hidden" name="id" value=\"{id}"><input type="submit" name="delcron" value="Suppr">"""
                f"""<input type="hidden" name="id" value="{id}">{'' if is_disabled else '<input type="hidden" name="disable">'}<input type="submit" name="disablecron" value=" {'Activer' if is_disabled else 'Désactiver'}">""")
                
    corps = [[dic[k] for k in keys] + [boutons(dic["id"], dic["is_disabled"])] for dic in lst]

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

    r += html_table(corps,
                    first_row = keys + ["Action"],
                    repeat_header = True,
                    very_last_row = nouv,
                    row_start = f"""<form action="admin?pwd={GLOBAL_PASSWORD}" method="post">""",
                    row_end = "</form>")

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
