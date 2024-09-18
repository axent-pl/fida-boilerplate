import json
import hashlib
import base64
import secrets
import redis
from typing import List
from sqlalchemy.orm import Session
from jwcrypto import jwt, jwk


import app.models as models
import app.dto as dto

sign_key = None

def get_sign_key() -> jwk.JWK:
    global sign_key
    if not sign_key:
        sign_key = jwk.JWK(generate='oct', size=256)
    return sign_key

def get_token_claims(token:str) -> dict:
    verified_jwt = jwt.JWT(key=get_sign_key(), jwt=str(token))
    claims = json.loads(verified_jwt.claims)
    return claims

def issue_token(claims: dict) -> dto.TokenDTO:
    token = jwt.JWT(header={'alg': 'HS256'}, claims=json.dumps(claims))
    token.make_signed_token(get_sign_key())
    return dto.TokenDTO(type='Bearer',access_token=token.serialize(),refresh_token=token.serialize())

def get_authorization_code(redirect_uri: str, client_id: str, username:str, code_db: redis.Redis, length: int = 32) -> str:
    data = json.dumps({
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'username': username,
    })
    authorization_code = secrets.token_urlsafe(length)
    code_db.set(authorization_code, data, ex=30)
    return authorization_code

def get_authorization_request(authorization_code: str, redirect_uri: str, client_id: str, code_db: redis.Redis) -> dict:
    data_json = code_db.get(authorization_code)
    if data_json is None:
        return None
    data = json.loads(data_json)
    if data.get('redirect_uri') != redirect_uri:
        return None
    if data.get('client_id') != client_id:
        return None
    
    code_db.delete(authorization_code)

    return data

