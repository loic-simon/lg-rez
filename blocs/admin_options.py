
def html_table(LL, beg_row, end_row):
    r = "<table style='border:1px solid black; border-collapse: collapse;'>"
    for L in LL:
        r += "<tr>{}<td style='border:1px solid black; padding:2pt;'>".format(beg_row)
        r += "</td><td style='border:1px solid black; padding:2pt;'>".join([str(l) for l in L])
        r += "</td>{}</tr>".format(end_row)
    r += "</table>"
    return r


def viewtable(d, p):
    r = ""

    table = p["table"]
    r += "<h2>Table : {}</h2>".format(table)

    cols = [column.key for column in globals()[table].__table__.columns]
    LE = globals()[table].query.all()
    LE = [[ e.__dict__[k] for k in cols ] for e in LE]

    tete = ["<b>{}</b>".format(ee) for ee in cols] + ["Action"]

    delButton = lambda x:"""<form action="admin?pwd={}" method="post"> <input type="hidden" name="table" value="{}"> <input type="hidden" name="id" value="{}"> <input type="submit" name="delitem" value="Suppr">""".format(GLOBAL_PASSWORD, table, x)

    corps = [e + [delButton(e[cols.index("messenger_user_id")])] for e in LE]

    itemDefault = { "messenger_user_id": random.randrange(1000000000),
                    "inscrit": True,
                    "nom": ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)),
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

    nouv = ["""<input type="text" name="{}" size="10cm" value={}>""".format(ee, itemDefault[ee]) for ee in cols] + ["""<input type="submit" name="additem" value="Créer">"""]


    r += html_table([tete] + corps + [nouv], """<form action="admin?pwd={}" method="post">
                                                <input type="hidden" name="table" value="{}">""".format(GLOBAL_PASSWORD, table),
                                            "</form>" )
    r += "<br />"

    return r


def additem(d, p):
    r = ""

    table = p["table"]
    r += "<h2>Ajout d'élément</h2>".format(table)
    r += "Table : {}\n\n".format(table)

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
    r += viewtable(d, p)

    return r


def delitem(d, p):
    r = ""

    table = p["table"]
    id = p["id"]
    r += "<h2>Suppression d'élément</h2>".format(table)
    r += "Table : {}, ID : {}\n\n".format(table, id)

    try:
        user_TDB = globals()[table].query.filter_by(messenger_user_id=id).one()
        db.session.delete(user_TDB)
        db.session.commit()
        r += "Suppression effectuée.\n\n"
    except NoResultFound:
        r += "Aucun résultat trouvé. Suppression non effectuée.\n\n"
    except MultipleResultsFound:
        r += "Plusieurs résultats trouvés. Suppression non effectuée.\n\n"

    r += viewtable(d, p)

    return r
