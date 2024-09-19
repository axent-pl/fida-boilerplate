from fastapi import Depends
from sqlalchemy.orm import Session

import app.components as components
import app.dto as dto
import app.models as models

class ClientService:

    def __init__(self, db: Session = Depends(components.get_db)):
        self.db: Session = db

    def authenticate(self, client_id: str, client_secret: str = None, client_assertion_type: str = None, client_assertion: str = None) -> bool:
        # authenticate client
        # * by client_secret
        # * by client_assertion_type='urn:ietf:params:oauth:client-assertion-type:jwt-bearer' and client_assertion
        return True

    def get_client(self, client_id: str) -> dto.ClientDTO:
        db_client = self.db.query(models.Client).filter(models.Client.id == client_id).first()
        if db_client is not None:
            return dto.ClientDTO(
                id = db_client.id,
                redirect_uri=db_client.redirect_uri
                )
        return None

    def upsert_client(self, client: dto.ClientDTO) -> dto.ClientDTO:
        db_client = self.db.query(models.Client).filter(models.Client.id == client.id).first()
        if db_client is None:
            new_client = models.Client(
                id=client.id,
                redirect_uri=client.redirect_uri
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
            self.db.commit()
            self.db.refresh(db_client)
            return dto.ClientDTO(
                    id=db_client.id,
                    redirect_uri=db_client.redirect_uri
                )