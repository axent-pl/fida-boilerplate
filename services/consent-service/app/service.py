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

def hash(string_list, hash_length=16):
    combined_string = '/'.join(string_list)
    hash_object = hashlib.sha256(combined_string.encode())
    hash_digest = hash_object.digest()
    base64_encoded = base64.urlsafe_b64encode(hash_digest).decode()
    return base64_encoded[:hash_length]

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
