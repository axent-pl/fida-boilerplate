import os

from uuid import uuid4
from contextlib import asynccontextmanager
from typing import Dict, List, Optional
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
from starlette.datastructures import URL

from app.database import Base, engine

import app.dto as dto
import app.service as service
import app.response_handlers as response_handlers
import app.components as components


CS_SESSION_SECRET = 'some-secret-???'


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=CS_SESSION_SECRET)

###############################################################################

@app.put('/admin/product-type/{urn}')
async def upsert_product_type(urn: str, product_type: dto.ProductTypeDTO, db: Session = Depends(components.get_db)):
     product_type.urn = urn
     return service.upsert_product_type(product_type=product_type, db=db)


@app.put("/admin/user/{username}")
async def upsert_user(username: str, user: dto.UserDTO, db: Session = Depends(components.get_db)):
    user.username = username
    return service.upsert_user(user=user, db=db)


@app.put("/admin/client/{id}")
async def upsert_client(id: str, client: dto.ClientDTO, db: Session = Depends(components.get_db)):
    client.id = id
    return service.upsert_client(client, db)

###############################################################################

@app.get('/authorization_grants')
async def get_authorization_grants(request: Request, client_id: str, scope: str, reponse_type: str, redirect_uri: str, db: Session = Depends(components.get_db), user: dto.UserDTO = Depends(components.get_user)):
    consents = service.get_client_user_consents(username=user.username, client_id=client_id, db=db)
    
    client = service.get_client(client_id=client_id, db=db)
    if not client:
        raise HTTPException(status_code=404, detail="Invalid client_id")
    if not redirect_uri.startswith(client.redirect_uri):
        raise HTTPException(status_code=404, detail="Invalid redirect_uri")
    
    return response_handlers.html({'consents':consents, 'client': client}, 'authorization-grants.html')

@app.post('/authorization_grants')
async def save_authorization_grants(request: Request, client_id: str, scope: str, reponse_type: str, redirect_uri: str, db: Session = Depends(components.get_db), user: dto.UserDTO = Depends(components.get_user)):
    consents = service.get_client_user_consents(username=user.username, client_id=client_id, db=db)
    
    client = service.get_client(client_id=client_id, db=db)
    if not client:
        raise HTTPException(status_code=404, detail="Invalid client_id")
    if not redirect_uri.startswith(client.redirect_uri):
        raise HTTPException(status_code=404, detail="Invalid redirect_uri")
    
    form_consents = await request.form()
    for consent in consents:
        if consent.key in form_consents:
            consent.status = form_consents[consent.key]
    updated_consents = service.upsert_client_user_consents(consents=consents, db=db)

    authorization_code = service.get_authorization_code(redirect_uri=redirect_uri, client_id=client_id)
    
    redirect_url = URL(redirect_uri)
    redirect_url = redirect_url.include_query_params(code=authorization_code)

    return RedirectResponse(url=str(redirect_url), status_code=303)


###############################################################################

# @app.get('/token')
# async def issue_token(request: Request, db: Session = Depends(components.get_db), session_db: Session = Depends(get_session_db)):
#     token =  service.sign_token({'custom':'foo'})
#     session_id = request.session.get('id') or str(uuid4())
#     request.session['id'] = session_id
#     session_db.set(session_id, token.access_token)
#     return token
