from flask import Flask, Blueprint, session, g
from models import db, User
import uuid
import os

""" This file contains the main app and sets some configuration
"""

app = Flask(__name__)
app.config['SECRET_KEY'] = str(uuid.uuid4())  
app.config['DATA_FOLDER'] = 'data/'
app.config['NFT_FOLDER'] = app.config['DATA_FOLDER'] + 'nft/'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024

app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+psycopg2://arnold:secret@db/fitty"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()    
    os.makedirs(os.path.join(app.config['NFT_FOLDER'], "generator"), exist_ok=True)
    os.makedirs(os.path.join(app.config['NFT_FOLDER'], "damaged"), exist_ok=True)

@app.before_request
def load_user():
    cur_user = User.query.get(session.get("user_id"))
    g.user = cur_user

@app.context_processor
def inject_user():
    return dict(user=g.user)
      
import routes.information
import routes.nft
import routes.user

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001)
