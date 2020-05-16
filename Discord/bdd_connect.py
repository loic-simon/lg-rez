import traceback

import tools

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile('../config.py')
db = SQLAlchemy(app)
exec(open("../models.py").read())
db.init_app(app)
    
    
def testbdd(ctx):
    tous = cache_TDB.query.all()
    ret = '\n - '.join([u.nom for u in tous])
    return tools.code_bloc(f"Liste des joueurs :\n - {ret}")


def rename(ctx):
    mots = ctx.message.content.split(maxsplit=2)    # sépare la commande en trois blocs ["!rename", "cible", "nom"]
    id = int(mots[1].strip())
    nom = mots[2].strip()
        
    try:
        u = cache_TDB.query.filter_by(messenger_user_id=id).one()
    except:
        return tools.code_bloc(f"Cible {id} non trouvée\n{traceback.format_exc()}")
    else:
        oldnom = u.nom
        u.nom = nom
        db.session.commit()
        return tools.code_bloc(f"Joueur {oldnom} renommé en {nom}.")


def do(ctx):
    txt = tools.command_arg(ctx)
    
    class Answer():
        def __init__(self):
            object.__init__(self)
            self.rep = ""
        
    a = Answer()
    
    exec(f"a.rep = {txt}", globals(), locals())

    return f"Entrée : {tools.code(txt)}\nSortie :\n{a.rep}"
