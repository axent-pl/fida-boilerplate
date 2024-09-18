import json
from jwcrypto import jwt, jwk
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



