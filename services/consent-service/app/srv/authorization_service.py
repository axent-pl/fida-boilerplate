import json
import secrets
import redis

from fastapi import Depends

import app.components as components
import app.config as config


class AuthorizationService:
    """Service for managing OAuth2 authorization codes using Redis."""

    def __init__(self, db: redis.Redis = Depends(components.get_code_db)):
        """
        Initialize the AuthorizationService with a Redis database connection.

        Args:
            db (redis.Redis): Redis database connection. Defaults to the dependency provided by FastAPI.
        """
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
