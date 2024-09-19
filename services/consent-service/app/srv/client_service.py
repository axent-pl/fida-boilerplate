import json
import time
from fastapi import Depends, requests
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jwcrypto import jwt, jwk

import app.components as components
import app.dto as dto
import app.models as models

from app.srv.token_service import TokenService

class ClientService:

    def __init__(self, db: Session = Depends(components.get_db), token_service: TokenService = Depends(TokenService)):
        self.db: Session = db
        self.token_service = token_service
        self.pwd_context: CryptContext = CryptContext(
            schemes=["bcrypt"], deprecated="auto")

    def _authenticate_with_client_secret(self, db_client: models.Client, client_secret: str) -> bool:
        return (db_client.secret_hash and self.pwd_context.verify(client_secret, db_client.secret_hash))
    
    def _authenticate_with_client_assertion(self, db_client: models.Client, client_assertion: str) -> bool:
        try:
            key = self.token_service.get_key(db_client.jwks_url)
            token = jwt.JWT(jwt=client_assertion, key=key)
            claims = json.loads(token.claims)

            if claims.get('iss') != db_client.issuer:
                return False
            
            # Verify expiration time (exp)
            current_time = int(time.time())
            if 'exp' in claims:
                exp = int(claims['exp'])
                if current_time > exp:
                    return False

            # Verify not before time (nbf)
            if 'nbf' in claims:
                nbf = int(claims['nbf'])
                if current_time < nbf:
                    return False
        except:
            return False
        
        return True

    def authenticate(self, client_id: str, client_secret: str = None, client_assertion_type: str = None, client_assertion: str = None) -> bool:
        db_client = self.db.query(models.Client).filter(
            models.Client.id == client_id).first()
        if db_client is None:
            return False

        if client_secret:
            return self._authenticate_with_client_secret(db_client=db_client, client_secret=client_secret)
        
        if client_assertion_type == 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer' and client_assertion:
            return self._authenticate_with_client_assertion(db_client=db_client, client_assertion=client_assertion)

        return True

    def get_client(self, client_id: str) -> dto.ClientDTO:
        db_client = self.db.query(models.Client).filter(
            models.Client.id == client_id).first()
        if db_client is not None:
            return dto.ClientDTO(
                id=db_client.id,
                redirect_uri=db_client.redirect_uri
            )
        return None

    def upsert_client(self, client: dto.ClientDTO) -> dto.ClientDTO:
        db_client = self.db.query(models.Client).filter(
            models.Client.id == client.id).first()
        if db_client is None:
            new_client = models.Client(
                id=client.id,
                redirect_uri=client.redirect_uri,
                secret_hash=self.pwd_context.hash(client.secret) if client.secret else None
            )
            self.db.add(new_client)
            self.db.commit()
            self.db.refresh(new_client)
            return dto.ClientDTO(
                id=new_client.id,
                redirect_uri=new_client.redirect_uri
            )
        else:
            db_client.redirect_uri = client.redirect_uri
            if client.secret:
                db_client.secret_hash=self.pwd_context.hash(client.secret)
            self.db.commit()
            self.db.refresh(db_client)
            return dto.ClientDTO(
                id=db_client.id,
                redirect_uri=db_client.redirect_uri
            )