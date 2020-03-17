from flask import request
from core import *
# from __init__ import app

# app = Flask(__name__)
# app.config.from_pyfile('config.py')

@app.route('/')
def index():
    return "Hello world !"

@app.route('/yikes/', methods=['GET', 'POST'])
def yikes():
    return "YIIIIIIKES"


@app.route('/admin', methods=['GET', 'POST'])
def holder_admin():
    return admin(request.args, request.form)

@app.route('/manual', methods=['GET'])
def holder_manual():
    return manual(request.args)



@app.route('/sync_TDB', methods=['GET'])
def holder_sync_TDB():
    return sync_TDB(request.args)




@app.route('/API_test', methods=['GET', 'POST'])
def holder_API_test():
    return API_test(request.json)
