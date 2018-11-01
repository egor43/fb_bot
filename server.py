from flask import Flask
from flask import request

import base64
import urllib
import json
import requests

app = Flask(__name__)

# User token
user_token = None
# Page token
page_token = None
# App token
app_token = None
# Last chat's identifier
last_sender_id = None
# App identifier
app_identifier = None
# App secret
app_secret = None
# Redirect uri
redirect_uri = None
# Page id
page_identifier = None

@app.route('/start/<application_id>/<application_secret>', methods=['GET'])
def set_default_settings(application_id, application_secret):
    """
    Setting Application Variables
    :param application_id: application identifier
    :param application_secret: application secret
    :return: server readiness message
    """
    if not application_secret:
        return "Error! App secret is none."
    if not application_id:
        return "Error! App identifier is none."

    application_id = decode_parameter(application_id)
    application_secret = decode_parameter(application_secret)
    global app_identifier, app_secret
    app_identifier = application_id
    app_secret = application_secret
    return "Server started!"

@app.route('/entry/<redirect>', methods=['GET'])
def entry(redirect):
    """
    Getting a link to the login request page via facebook
    :param redirect: webhook url
    :return: link to the login request page via facebook
    """
    redirect = decode_parameter(redirect)
    if not redirect:
        return "Error! Redirect uri is none."
    if not app_identifier:
        return "Error! App identifier is none."
    global redirect_uri
    redirect_uri = redirect
    login_url = 'https://www.facebook.com/v3.2/dialog/oauth?' \
                'client_id={app_id}' \
                '&redirect_uri={redirect_uri}' \
                '&state={state_param}' \
                '&scope=manage_pages,read_page_mailboxes,pages_messaging,pages_messaging_subscriptions'
    login_url = login_url.format(app_id=app_identifier, redirect_uri=redirect_uri, state_param="my_state")
    return login_url

@app.route('/setappid/<app_id>', methods=['GET'])
def set_app_id(app_id):
    """
    Sets the application identifier
    :param app_id: application identifier
    :return: setted application identifier
    """
    app_id = decode_parameter(app_id)
    if not app_id:
        return "Error! Application identifier is none."

    global app_identifier
    app_identifier = app_id
    return app_identifier

@app.route('/setapplicationsecret/<application_secret>', methods=['GET'])
def set_application_secret(application_secret):
    """
    Sets the client secret
    :param application_secret: client secret
    :return: setted client secret
    """
    application_secret = decode_parameter(application_secret)
    if not application_secret:
        return "Error! Application identifier is none."

    global app_secret
    app_secret = application_secret
    return app_secret

@app.route('/connect', methods=['GET', 'POST'])
def connect_user():
    """
    Processing Facebook login request
    :return: setted user token
    """
    code = request.args.get("code", None)
    if not code:
        print(str(request.args))
        return "Error! Parameter code is none."
    if not redirect_uri:
        return "Error! Redirect uri is none."
    if not app_identifier:
        return "Error! App identifier is none."
    if not app_secret:
        return "Error! Client secret is none."

    header = {'Content-Type': 'application/json;charset=utf-8'}
    request_address = 'https://graph.facebook.com/v3.2/oauth/access_token?' \
                      'client_id={app_id}' \
                      '&redirect_uri={redirect_uri}' \
                      '&client_secret={app_secret}' \
                      '&code={code}'
    request_address = request_address.format(app_id=app_identifier,
                                             redirect_uri=redirect_uri,
                                             app_secret=app_secret,
                                             code=code)
    response = requests.get(request_address, headers=header)
    json_data = json.loads(response.text)
    access_token = json_data.get("access_token", None)
    if not access_token:
        print(str(response.text))
        return "Error! Access token is none."
    global user_token
    user_token = access_token
    return user_token

@app.route('/getpagetoken/<page_id>', methods=["GET"])
def get_page_token(page_id):
    """
    Getting a page access token
    :param page_id: page identifier
    :return: setted page identifire
    """
    if not page_id:
        return "Error! Page identifier is none."
    page_id = decode_parameter(page_id)
    header = {'Content-Type': 'application/json;charset=utf-8'}
    request_address = 'https://graph.facebook.com/v3.2/{page_id}?fields=access_token&access_token={token}'
    request_address = request_address.format(page_id=page_id, token=user_token)
    response = requests.get(request_address, headers=header)
    json_data = json.loads(response.text)
    access_token = json_data.get("access_token", None)
    if not access_token:
        print(str(response.text))
        return "Error! Access token is none."
    global page_token
    page_token = access_token
    global page_identifier
    page_identifier = page_id
    return page_identifier

@app.route('/getapptoken', methods=["GET"])
def get_app_token():
    """
    Getting application access token
    :return: setted application token
    """
    header = {'Content-Type': 'application/json;charset=utf-8'}
    request_address = 'https://graph.facebook.com/oauth/access_token' \
                      '?client_id={app_id}' \
                      '&client_secret={app_secret}' \
                      '&redirect_uri={redirect_uri}' \
                      '&grant_type=client_credentials'
    request_address = request_address.format(app_id=app_identifier,
                                             app_secret=app_secret,
                                             redirect_uri="none")
    response = requests.get(request_address, headers=header)
    print(str(request_address))
    json_data = json.loads(response.text)
    access_token = json_data.get("access_token", None)

    if not access_token:
        return "Error! Access token is none."
    global app_token
    app_token = access_token

    return app_token

@app.route('/setwebhook/<callback>', methods=["GET"])
def set_webhook(callback):
    """
    Installing the webhook for the application
    :param callback: webhook for the application
    :return: server response
    """
    if not callback:
        return "Error! No callback."
    if not app_identifier:
        return "Error! No app identifier."
    callback = decode_parameter(callback)
    header = {'Content-Type': 'application/json;charset=utf-8'}
    request_address = 'https://graph.facebook.com/v3.2/{app_id}/subscriptions?access_token={app_token}'
    request_address = request_address.format(app_id=app_identifier, app_token=app_token)
    parameter = 'object=page' \
                '&callback_url={callback}' \
                '&fields=conversations%2Cfeed%2Cmessages' \
                '&include_values=true' \
                '&verify_token=thisisaverifystring'.format(callback=callback)
    response = requests.post(request_address, data=parameter, headers=header)
    print(str(response))
    return response.text

@app.route('/subscribepage', methods=["GET"])
def subscribe_page():
    """
    Signs the page for application webhook
    :return: server response
    """
    if not page_token:
        return "Error! No page token."
    if not page_identifier:
        return "Error! No page identifier."
    header = {'Content-Type': 'application/json;charset=utf-8'}
    request_address = 'https://graph.facebook.com/v3.2/{page_id}/subscribed_apps?access_token={page_token}'
    request_address = request_address.format(page_id=page_identifier, page_token=page_token)
    parameter = 'subscribed_fields=conversations%2Cfeed%2Cmessages'
    response = requests.post(request_address, data=parameter, headers=header)
    print(str(response))
    return response.text

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
        return "Ok"
    messaging = entry[0].get('messaging')
    if not messaging:
        print('Error! Not field "messaging" in incoming request')
        return "Ok"
    sender = messaging[0].get('sender')
    if not sender:
        print('Error! Not field "sender" in incoming request')
        return "Ok"
    global last_sender_id
    old_sender = last_sender_id
    last_sender_id = sender.get('id')
    if not last_sender_id:
        print('Error! Could not get sender id.')
        return "Ok"
    if old_sender != last_sender_id:
        send_message("Hello! You are welcomed by the bot.")
    return 'Ok'

@app.route('/webhook', methods=['GET', 'POST'])
def recieve_webhook():
    """
    Recives webhook
    :return: Always return the answer: value from field 'hub.challenge'
    """
    global user_token
    user_token = request.args.get('hub.verify_token', "")
    print(user_token)
    challenge = request.args.get("hub.challenge", "")
    return challenge

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
    request_address = 'https://graph.facebook.com/v2.6/me/messages?access_token={page_token}'.format(page_token=page_token)
    response = requests.post(request_address, data=json.dumps(data), headers=header)
    print(str(response))
    return response.text

@app.route('/userinfo', methods=['GET'])
def get_userinfo():
    """
    Getting last user info
    :return: last user info
    """
    header = {'Content-Type': 'application/json;charset=utf-8'}
    request_address = 'https://graph.facebook.com/{psid}?access_token={token}'.format(psid=last_sender_id, token=user_token)
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