from flask import request
from core import *
from flask import jsonify

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code

    def to_dict(self):
        return self.message

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route('/')
def index():
    return "Hello world !"

@app.route('/admin', methods=['GET', 'POST'])
def holder_admin():
    return admin(request.args, request.form)

@app.route('/manual', methods=['GET'])
def holder_manual():
    return manual(request.args)

@app.route('/sync_TDB', methods=['GET'])
def holder_sync_TDB():
    r = sync_TDB(request.args)
    if isinstance(r, tuple) and isinstance(r[0],int) and isinstance(r[1],str):
        raise InvalidUsage(r[1], status_code=r[0])
    else:
        return r
        
@app.route('/cron_call', methods=['GET'])
def holder_cron_call():
    r = cron_call(request.args)
    if isinstance(r, tuple) and isinstance(r[0],int) and isinstance(r[1],str):
        raise InvalidUsage(r[1], status_code=r[0])
    else:
        return r
        
