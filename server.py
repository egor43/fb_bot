from flask import Flask
from flask import request

import base64
import urllib
import json
import requests

app = Flask(__name__)

# Group's token
token = None
# Last chat's identifier
last_sender_id = None

@app.route('/webhook', methods=['POST'])
def recieve_message():
    """
    Recives messages
    :return: Always return the answer: OK
    """
    json_data = json.loads(request.data.decode())
    print(str(json_data))
    entry = json_data.get('entry')
    if not entry:
        print('Error! Not field "entry" in incoming request')
    messaging = entry[0].get('messaging')
    if not messaging:
        print('Error! Not field "messaging" in incoming request')
    sender = messaging[0].get('sender')
    if not sender:
        print('Error! Not field "sender" in incoming request')
    global last_sender_id
    if sender.get('id') != last_sender_id:
        last_sender_id = sender.get('id')
        send_message("Hello! You are welcomed by the bot.")
    if not last_sender_id:
        print('Error! Could not get sender id.')
    return 'Ok'

@app.route('/webhook', methods=['GET', 'POST'])
def recieve_webhook():
    """
    Recives webhook
    :return: Always return the answer: value from field 'hub.challenge'
    """
    global token
    token = request.args.get('hub.verify_token', "")
    print(token)
    challenge = request.args.get("hub.challenge", "")
    return challenge

@app.route('/settoken/<bot_token>', methods=['GET'])
def set_token(bot_token):
    """
    Sets the bot token
    :param bot_token: bot token
    :return: set bot token
    """
    bot_token = decode_parameter(bot_token)
    if not bot_token:
        return "Error! Token is none."
    global token
    token = bot_token
    return token

@app.route('/sendmessage/<message>', methods=['GET'])
def send_message(message):
    """
    Send message into last chat
    :param message: meaasge
    :return: response from server
    """
    if not message:
        return "Error! No message."
    if not last_sender_id:
        return "Error! No last chat identifier."
    header = {'Content-Type': 'application/json;charset=utf-8'}
    data = {'messaging_type': 'RESPONSE', 'recipient': {'id': last_sender_id}, 'message': {'text': message}}
    request_address = 'https://graph.facebook.com/v2.6/me/messages?access_token={token}'.format(token=token)
    response = requests.post(request_address, data=json.dumps(data), headers=header)
    print(str(response))
    return response.text

@app.route('/userinfo', methods=['GET'])
def get_webhook():
    """
    Getting last user info
    :return: last user info
    """
    header = {'Content-Type': 'application/json;charset=utf-8'}
    request_address = 'https://graph.facebook.com/{psid}?access_token={token}'.format(psid=last_sender_id, token=token)
    response = requests.get(request_address, headers=header)
    return response.text

def decode_parameter(parameter):
    """
    Decoding parameter received in url
    :param parameter: parameter received in url
    :return: decoded parameter
    """
    if not parameter:
        return None
    parameter_b64 = urllib.parse.unquote(parameter)
    return base64.b64decode(parameter_b64).decode()

if __name__ == '__main__':
    app.run()