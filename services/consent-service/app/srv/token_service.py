from fastapi import Depends, requests
from sqlalchemy.orm import Session
from jwcrypto import jwk

class TokenService:

    def __init__(self):
        pass

    def get_key(self, jwks_url:str) -> jwk.JWKSet:
        jwks_response = requests.get(jwks_url)
        jwks_response.raise_for_status()
        jwks_json = jwks_response.text
        return jwk.JWKSet.from_json(jwks_json)