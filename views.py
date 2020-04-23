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
        
        
# @app.route('/sync_Chatfuel', methods=['GET', 'POST'])
# def holder_sync_Chatfuel():
#     return sync_Chatfuel(request.args, request.json)
    
    
@app.route('/cron_call', methods=['GET'])
def holder_cron_call():
    r = cron_call(request.args)
    if isinstance(r, tuple) and isinstance(r[0],int) and isinstance(r[1],str):
        raise InvalidUsage(r[1], status_code=r[0])
    else:
        return r
    
    
@app.route('/liste_joueurs', methods=['GET'])
def holder_liste_joueurs():
    return liste_joueurs(request.args)
    
    
@app.route('/choix_cible', methods=['GET', 'POST'])
def holder_choix_cible():
    return choix_cible(request.args, request.json, request.url_root)
    
@app.route('/envoi_mp', methods=['GET', 'POST'])
def holder_envoi_mp():
    r = envoi_mp(request.args, request.json)
    if isinstance(r, tuple) and isinstance(r[0],int) and isinstance(r[1],str):
        raise InvalidUsage(r[1], status_code=r[0])
    else:
        return r
        
        
@app.route('/media_renderer', methods=['GET', 'POST'])
def holder_media_renderer():
    return media_renderer(request.args, request.json)




@app.route('/API_test', methods=['GET', 'POST'])
def holder_API_test():
    return API_test(request.args, request.json)

@app.route('/Hermes_test', methods=['GET'])
def holder_Hermes_test():
    return Hermes_test(request.args)

# 
# @app.route('/testbot', methods=['GET', 'POST'])
# def holder_testbot():
#     ACCESS_TOKEN="EAAKfdOGXd00BAIiZAZBV6ha7fHO4veDz3wMKD8yGZAlALqG0S4FZCZBPrcloFrICqCq9D7C0DwSgyGmRDgycSsaHrvpP8TJtyT1xEf71ZCJSzPpM5mcf5DDBmJUcEo98OBoWWBP8URGopJ88CZBkEPlZAKRbWhbBqGjMoggNR633sWGb3SsuaZAKZB"
# 
#     log = ""
# 
#     m = request.method
#     a = request.args
#     f = request.form
#     j = request.json
#     d = request.data
# 
#     if "hub.challenge" in a:
#         rep = d["hub.challenge"]
#     else:
#         rep = 'rep'
# 
#     log += f"> {time.ctime()} : appel testbot\nrequest:{request}json:{j}\n"
#     # log += f"> {time.ctime()} : appel testbot\nrequest:{request}\nmethod:{m}\nargs:{a}\nform:{f}\njson:{j}\ndata:{d}\nrep:{rep}\n\n"
# 
#     # Handles messages events
#     def handleMessage(sender_psid, received_message, log):
#         log += f"\nMessage: id:{sender_psid}, message:{received_message}\n"
#         log = callSendAPI(sender_psid, received_message.upper(), log)
# 
#         return log
# 
#     # Handles messaging_postbacks events
#     def handlePostback(sender_psid, received_postback):
#         pass    
# 
#     # Sends response messages via the Send API
#     def callSendAPI(sender_psid, response, log):
#         params = {"access_token": ACCESS_TOKEN}
#         request_body = {
#             "recipient": {"id": sender_psid},
#             "message": {"text": response},
#         }
#         log += f"Answer: {request_body}\n\n"
#         rep = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, json=request_body)
# 
#         log += rep.text
#         return log
# 
# 
#     if "entry" in j:
#         entry = j["entry"][0]
#         if "messaging" in entry:
#             messaging = entry["messaging"][0]
#             if "sender" in messaging and "message" in messaging:
#                 id = messaging["sender"]["id"]        
#                 message = messaging["message"]["text"]
#                 log = handleMessage(id, message, log)
# 
#     with open(f"logs/testbot/{time.strftime('%Y-%m-%d')}.log", 'a+') as fich:
#         fich.write(log+"\n\n")
