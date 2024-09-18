from typing import List
from fastapi import Depends
from sqlalchemy.orm import Session

import app.components as components
import app.dto as dto
import app.models as models
import app.utils as utils

from app.srv.product_type_service import ProductTypeService

class ConsentService:

    def __init__(self, db: Session = Depends(components.get_db), product_type_service: ProductTypeService = Depends(ProductTypeService)):
        self.db: Session = db
        self.product_type_service: ProductTypeService = product_type_service

    def upsert(self, consents: List[dto.ConsentDTO]) -> List[dto.ConsentDTO]:
        for consent in consents:
            db_consent = self.db.query(models.Consent).filter(
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
                self.db.add(new_consent)
                self.db.flush()
            else:
                db_consent.status = consent.status
        self.db.commit()
        return consents
    
    def find_all_by_username_and_client_id(self, username: str, client_id: str, refresh: bool = True) -> List[dto.ConsentDTO]:
        all_consents = {}
        if refresh:
            product_types = self.product_type_service.get_all()
            for product_type in product_types:
                key = utils.urlsafe_hash([username, client_id, product_type.urn])
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
                key = utils.urlsafe_hash([username, client_id, product_type.urn, product_id])
                all_consents[key] = dto.ConsentDTO(
                    key=key,
                    username=username,
                    client_id=client_id,
                    product_type_urn=product_type.urn,
                    type=dto.ConsentTypeEnum.specific,
                    product_id=product_id,
                    status=None,
                )
        client_user_consents = self.db.query(models.Consent).filter(
            models.Consent.client_id == client_id,
            models.Consent.user_username == username
        ).all()
        for db_consent in client_user_consents:
            key = utils.urlsafe_hash([username, client_id, db_consent.product_type_urn, db_consent.product_id]) if db_consent.product_id else utils.urlsafe_hash([username, client_id, db_consent.product_type_urn])
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