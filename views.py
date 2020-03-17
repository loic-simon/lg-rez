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

@app.route('/manualdelete', methods=['GET', 'POST'])
def holder_manualdelete():
    return manualdelete(request.args, request.form)
    
@app.route('/viewtable', methods=['GET', 'POST'])
def holder_viewtable():
    return viewtable(request.args, request.form)
    
@app.route('/getsetcell', methods=['GET', 'POST'])
def holder_getsetcell():
    return getsetcell(request.args, request.form)




@app.route('/API_test', methods=['GET', 'POST'])
def holder_API_test():
    return API_test(request.json)
