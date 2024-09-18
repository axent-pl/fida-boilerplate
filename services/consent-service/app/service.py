import json
import hashlib
import base64
import secrets
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from jwcrypto import jwt, jwk
from jwcrypto.common import json_decode

import  app.models as models
import  app.dto as dto

###############################################################################

def find_all_sign_keys():
    pass

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

def sign_token(claims: dict) -> dto.TokenDTO:
    token = jwt.JWT(header={'alg': 'HS256'}, claims=json.dumps(claims))
    token.make_signed_token(get_sign_key())
    return dto.TokenDTO(type='Bearer',access_token=token.serialize(),refresh_token=token.serialize())

def find_all_consents(username: str, client_id: str, db: Session) -> List[dto.ConsentDTO]:
    db_consents = db.query(models.Consent).filter(
        models.Consent.user_id == db.query(models.User).filter(models.User.username == username).first().id,
        models.Consent.client_id == db.query(models.Client).filter(models.Client.client_external_id == client_id).first().id
    ).all()
    return db_consents

###############################################################################

def get_authorization_code(redirect_uri: str, client_id: str, length: int = 32):
    authorization_code = secrets.token_urlsafe(length)
    return authorization_code

def hash(string_list, hash_length=16):
    combined_string = '/'.join(string_list)
    hash_object = hashlib.sha256(combined_string.encode())
    hash_digest = hash_object.digest()
    base64_encoded = base64.urlsafe_b64encode(hash_digest).decode()
    return base64_encoded[:hash_length]

def get_client(client_id:str, db: Session) -> dto.ClientDTO:
    db_client = db.query(models.Client).filter(models.Client.id == client_id).first()
    if db_client is not None:
        return dto.ClientDTO(
            id = db_client.id,
            redirect_uri=db_client.redirect_uri
            )
    return None

def get_all_product_types(db: Session) -> dto.ProductTypeDTO:
    product_types = []
    db_product_types = db.query(models.ProductType).all()
    for db_product_type in db_product_types:
        product_type = dto.ProductTypeDTO(
            urn=db_product_type.urn,
            name=db_product_type.name
        )
        product_types.append(product_type)
    return product_types

def upsert_client_user_consents(consents: List[dto.ConsentDTO], db: Session) -> List[dto.ConsentDTO]:
    for consent in consents:
        db_consent = db.query(models.Consent).filter(
            models.Consent.client_id == consent.client_id,
            models.Consent.user_username == consent.username,
            models.Consent.product_type_urn == consent.product_type_urn,
            models.Consent.product_id == consent.product_id
        ).first()
        if db_consent is None:
            new_consent = models.Consent(
                client_id=consent.client_id,
                user_username=consent.username,
                product_type_urn=consent.product_type_urn,
                product_id=consent.product_id,
                status=consent.status
            )
            db.add(new_consent)
            db.flush()
        else:
            db_consent.status = consent.status
    db.commit()
    return consents
    

def get_client_user_consents(username: str, client_id: str, db: Session, refresh: bool = True) -> List[dto.ConsentDTO]:
    all_consents = {}
    if refresh:
        product_types = get_all_product_types(db)
        for product_type in product_types:
            key = hash([username, client_id, product_type.urn])
            all_consents[key] = dto.ConsentDTO(
                key=key,
                username=username,
                client_id=client_id,
                product_type_urn=product_type.urn,
                type=dto.ConsentTypeEnum.generic,
                product_id=None,
                status=None,
            )
            # refresh => load user products
            product_id = 'PL10105000997603123456789123'
            key = hash([username, client_id, product_type.urn, product_id])
            all_consents[key] = dto.ConsentDTO(
                key=key,
                username=username,
                client_id=client_id,
                product_type_urn=product_type.urn,
                type=dto.ConsentTypeEnum.specific,
                product_id=product_id,
                status=None,
            )
    client_user_consents = db.query(models.Consent).filter(
        models.Consent.client_id == client_id,
        models.Consent.user_username == username
    ).all()
    for db_consent in client_user_consents:
        key = hash([username, client_id, db_consent.product_type_urn, db_consent.product_id]) if db_consent.product_id else hash([username, client_id, db_consent.product_type_urn])
        all_consents[key] = dto.ConsentDTO(
            key=key,
            username=username,
            client_id=client_id,
            product_type_urn=db_consent.product_type_urn,
            type=dto.ConsentTypeEnum.generic if not db_consent.product_id else dto.ConsentTypeEnum.specific,
            product_id=db_consent.product_id,
            status=db_consent.status,
        )
    return list(all_consents.values())

def upsert_user(user: dto.UserDTO, db: Session) -> dto.UserDTO:
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user is None:
        new_user = models.User(username=user.username)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return dto.UserDTO(
            username=new_user.username
        )
    else:
        return dto.UserDTO(
            username=db_user.username
        )

def upsert_product_type(product_type: dto.ProductTypeDTO, db: Session) -> dto.ProductTypeDTO:
    db_product_type = db.query(models.ProductType).filter(models.ProductType.urn == product_type.urn).first()
    if db_product_type is None:
        new_product_type = models.ProductType(urn=product_type.urn, name=product_type.name)
        db.add(new_product_type)
        db.commit()
        db.refresh(new_product_type)
        return dto.ProductTypeDTO(
            urn=new_product_type.urn,
            name=new_product_type.name
        )
    else:
        db_product_type.name = product_type.name
        db.commit()
        db.refresh(db_product_type)
        return dto.ProductTypeDTO(
            urn=db_product_type.urn,
            name=db_product_type.name
        )

def upsert_client(client: dto.ClientDTO, db: Session) -> dto.ClientDTO:
    db_client = db.query(models.Client).filter(models.Client.id == client.id).first()
    if db_client is None:
        new_client = models.Client(
            id=client.id,
            redirect_uri=client.redirect_uri
        )
        db.add(new_client)
        db.commit()
        db.refresh(new_client)
        return dto.ClientDTO(
            id=new_client.id,
            redirect_uri=new_client.redirect_uri
        )
    else:
        db_client.redirect_uri = client.redirect_uri
        db.commit()
        db.refresh(db_client)
        return dto.ClientDTO(
                id=db_client.id,
                redirect_uri=db_client.redirect_uri
            )