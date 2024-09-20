import datetime
import json
import secrets
import time
import redis

from fastapi import Depends, requests
from sqlalchemy.orm import Session
from jwcrypto import jwk, jwt

import app.dto as dto
import app.components as components
import app.config as config

class OAuthService:

    generated_key: jwk.JWK = jwk.JWK(generate='oct', size=256)

    def __init__(self, db: redis.Redis = Depends(components.get_code_db)):
        self.db: redis.Redis = db

    def get_authorization_code(
            self,
            redirect_uri: str,
            client_id: str,
            username: str,
            length: int = config.settings.CS_CODE_LENGTH
    ) -> str:
        """
        Generate and store an authorization code associated with the given parameters.

        Args:
            redirect_uri (str): The redirect URI provided by the client.
            client_id (str): The client ID.
            username (str): The username of the authenticated user.
            length (int, optional): Desired length of the generated authorization code.
                Defaults to config.settings.CS_CODE_LENGTH.

        Returns:
            str: The generated authorization code.
        """
        data = json.dumps({
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'username': username,
        })
        authorization_code = secrets.token_urlsafe(length)
        self.db.set(authorization_code, data,
                    ex=config.settings.CS_CODE_TTL_SECONDS)
        return authorization_code

    def get_authorization_request(
            self,
            authorization_code: str,
            redirect_uri: str,
            client_id: str
    ) -> dict:
        """
        Retrieve and validate the authorization request associated with the authorization code.

        Args:
            authorization_code (str): The authorization code to validate.
            redirect_uri (str): The redirect URI to validate against the stored one.
            client_id (str): The client ID to validate against the stored one.

        Returns:
            dict: The stored data associated with the authorization code if valid, None otherwise.
        """
        data_bytes = self.db.get(authorization_code)
        if data_bytes is None:
            return None
        
        try:
            data_str = data_bytes.decode('utf-8')
            data = json.loads(data_str)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None

        if data.get('redirect_uri') != redirect_uri:
            return None
        if data.get('client_id') != client_id:
            return None

        self.db.delete(authorization_code)
        return data

    def get_key(self, jwks_url:str = None, private_key_pem_path:str = None, self_generated: bool = False) -> jwk.JWKSet | jwk.JWK:
        if jwks_url is not None:
            jwks_response = requests.get(jwks_url)
            jwks_response.raise_for_status()
            jwks_json = jwks_response.text
            return jwk.JWKSet.from_json(jwks_json)
        elif private_key_pem_path is not None:
            with open(private_key_pem_path, 'rb') as key_file:
                private_key_pem = key_file.read()
                private_key_jwk = jwk.JWK.from_pem(private_key_pem)
                return jwk.JWK(**{'kty': private_key_jwk.get('kty'), 'n': private_key_jwk.get('n'), 'e': private_key_jwk.get('e')})
        elif self_generated:
            return self.generated_key
        return None
    
    def get_token(self, key:jwk.JWK, issuer_uri:str, username: str, client_id: str, claims: dict) -> dto.TokenDTO:
        now = datetime.datetime.now(datetime.timezone.utc)

        access_token_expiration = now + datetime.timedelta(minutes=15)
        access_token_claims = {
            'iss': issuer_uri,
            'sub': username,
            'aud': client_id,
            'exp': int(access_token_expiration.timestamp()),
            'iat': int(now.timestamp()),
            'typ': 'Bearer',
            'preferred_username': username,
        }
        if claims:
            access_token_claims.update(claims)
        access_token = jwt.JWT(header={'alg': 'HS256'}, claims=json.dumps(access_token_claims))
        access_token.make_signed_token(key)

        refresh_token_expiration = now + datetime.timedelta(days=30) 
        refresh_token_claims = {
            'iss': issuer_uri,
            'sub': username,
            'aud': client_id,
            'exp': int(refresh_token_expiration.timestamp()),
            'iat': int(now.timestamp()),
            'typ': 'Refresh',
        }
        refresh_token = jwt.JWT(header={'alg': 'HS256'}, claims=refresh_token_claims)
        refresh_token.make_signed_token(key)

        return dto.TokenDTO(type='Bearer', access_token=access_token.serialize(), refresh_token=refresh_token.serialize())

    def validate_serialized_token(self, token:str, key:jwk.JWKSet | jwk.JWK) -> bool:
        try:
            jwt_token = jwt.JWT(jwt=token, key=key)
            claims = json.loads(jwt_token.claims)

            current_time = int(time.time())
            if 'exp' in claims:
                exp = int(claims['exp'])
                if current_time > exp:
                    return False

            if 'nbf' in claims:
                nbf = int(claims['nbf'])
                if current_time < nbf:
                    return False
        except:
            return False
        
        return True
    
    def extract_serialized_token_claims(self, token:str) -> dict:
        jwt_token = jwt.JWT(jwt=token)
        return json.loads(jwt_token.claims)