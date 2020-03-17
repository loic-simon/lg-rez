from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile('config.py')

exec(open("./views.py").read())

if __name__ == "__main__":
    app.run()


db = SQLAlchemy(app)

exec(open("./models.py").read())

if __name__ == '__main__':
    db.init_app(app)
