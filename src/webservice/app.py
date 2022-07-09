from flask import Flask, request, make_response, render_template
import base64, hmac, hashlib, struct, sys, time

import random
import string
import json
import re

app = Flask(__name__)

def totp(key, interval=60, now=time.time()):
    # key = base64.b32decode(key.upper() + '=' * ((8 - len(key)) % 8))
    print(now)
    try:
        key = key.encode()
        counter1 = struct.pack('>Q', int(now / interval))

        mac1 = hmac.new(key, counter1, hashlib.sha256).digest()
        password = base64.b32encode(mac1).decode().replace("=", "")

    except Exception as e:
        print(e)
        password = None
    return password


@app.route("/", methods=['GET', 'POST'])
def index():
    secrets_cookie = request.cookies.get('secrets')
    secrets = json.loads(secrets_cookie) if secrets_cookie else None

    if request.method == 'POST':       
        s = request.form['s']    
        n = request.form['n']
        
        if not s or len(s) != 12:
            error = "Token not valid"
            return render_template("index.html", secrets=secrets, error=error)

        if not n:
            n = ""

        if secrets:
            secrets.append({"s":s, "n":n})
        else:
            secrets = [{"s":s, "n":n}]

    resp = make_response(render_template("index.html", secrets=secrets))
    resp.set_cookie('secrets', json.dumps(secrets))
    return resp

@app.route('/get_password', methods=['POST'])
def setcookie():         
    s = request.form['s']
    if not s or len(s) != 12:
        return "", 500
    password = totp(s, now=time.time())
    if not password:
        return "", 500
    return password

if __name__ == '__main__':
    app.run()
