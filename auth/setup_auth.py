# auth/setup_auth.py

import os
import webbrowser
import hashlib
import base64
import secrets
import requests
from flask import Flask, request
from dotenv import load_dotenv, set_key

# Load env variables
load_dotenv()

app = Flask(__name__)

# Config
CLIENT_ID = os.getenv("ETSY_API_KEY")
REDIRECT_URI = "http://localhost:3000/callback"
AUTH_URL = "https://www.etsy.com/oauth/connect"
TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
ENV_FILE = ".env"

# Helper for PKCE
def generate_pkce():
    code_verifier = secrets.token_urlsafe(32)
    m = hashlib.sha256()
    m.update(code_verifier.encode('ascii'))
    code_challenge = base64.urlsafe_b64encode(m.digest()).decode('ascii').rstrip('=')
    return code_verifier, code_challenge

# Global storage for verifier
verifier_storage = {}

@app.route("/")
def home():
    verifier, challenge = generate_pkce()
    state = secrets.token_hex(16)
    verifier_storage['current'] = verifier
    
    # Permissions
    scopes = "address_r address_w billing_r cart_r cart_w email_r favorites_r favorites_w feedback_r listings_d listings_r listings_w profile_r profile_w recommend_r recommend_w shops_r shops_w transactions_r transactions_w"

    oauth_url = (
        f"{AUTH_URL}?"
        f"response_type=code&"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope={scopes}&"
        f"state={state}&"
        f"code_challenge={challenge}&"
        f"code_challenge_method=S256"
    )
    
    return f'''
    <h1>Etsy Python Auth Setup</h1>
    <p>Click below to authorize and generate the Refresh Token.</p>
    <a href="{oauth_url}"><button style="font-size:16px; padding:10px;">Connect with Etsy</button></a>
    '''

@app.route("/callback")
def callback():
    code = request.args.get("code")
    error = request.args.get("error")
    
    if error: return f"Error: {error}"

    payload = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "code": code,
        "code_verifier": verifier_storage['current']
    }
    
    response = requests.post(TOKEN_URL, data=payload)
    
    if response.status_code == 200:
        tokens = response.json()
        set_key(ENV_FILE, "ETSY_REFRESH_TOKEN", tokens['refresh_token'])
        set_key(ENV_FILE, "ETSY_ACCESS_TOKEN", tokens['access_token'])
        
        return f'''
        <h1>Success!</h1>
        <p>Refresh Token saved in .env</p>
        <p>User ID: {tokens['access_token'].split('.')[0]}</p>
        <p>You can close this window now.</p>
        '''
    else:
        return f"Error getting token: {response.text}"

if __name__ == "__main__":
    print(f"--- Setup Auth ---")
    if not CLIENT_ID:
        print("ERROR: Missing ETSY_API_KEY in .env")
    else:
        print("Open: http://localhost:3000")
        webbrowser.open("http://localhost:3000")
        app.run(port=3000)