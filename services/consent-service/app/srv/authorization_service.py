import json
import secrets
import redis

from fastapi import Depends

import app.components as components
import app.config as config

class AuthorizationService:

    def __init__(self, db: redis.Redis = Depends(components.get_code_db)):
        self.db: redis.Redis = db

    def get_authorization_code(self, redirect_uri: str, client_id: str, username:str, length: int = config.settings.CS_CODE_LENGTH) -> str:
        data = json.dumps({
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'username': username,
        })
        authorization_code = secrets.token_urlsafe(length)
        self.db.set(authorization_code, data, ex=config.settings.CS_CODE_TTL_SECONDS)
        return authorization_code
    
    def get_authorization_request(self, authorization_code: str, redirect_uri: str, client_id: str) -> dict:
        data_json = self.db.get(authorization_code)
        if data_json is None:
            return None
        data = json.loads(data_json)
        if data.get('redirect_uri') != redirect_uri:
            return None
        if data.get('client_id') != client_id:
            return None
        
        self.db.delete(authorization_code)

        return data