import os
from uuid import uuid4
import redis

from fastapi import Depends, Request

import app.database as database
import app.dto as dto
import app.config as config

async def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_session_db():
    redis_client = redis.Redis.from_url(config.settings.CS_SESSION_DB_ORIGIN)
    try:
        yield redis_client
    finally:
        redis_client.close()

async def get_code_db():
    redis_client = redis.Redis.from_url(config.settings.CS_CODE_DB_ORIGIN)
    try:
        yield redis_client
    finally:
        redis_client.close()

async def get_user(request: Request, session_db: redis.Redis = Depends(get_session_db)) -> dto.UserDTO:
    return dto.UserDTO(username='jane-bar-com')
    session_id = request.session.get('id') or str(uuid4())
    request.session['id'] = session_id
    token = session_db.get(session_id)
    return service.get_token_claims(token.decode('utf-8')) if token else None