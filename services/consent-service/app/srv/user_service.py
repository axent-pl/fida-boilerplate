from fastapi import Depends
from sqlalchemy.orm import Session

import app.components as components
import app.dto as dto
import app.models as models

class UserService:

    def __init__(self, db: Session = Depends(components.get_db)):
        self.db = db

    def upsert_user(self, user: dto.UserDTO) -> dto.UserDTO:
        db_user = self.db.query(models.User).filter(models.User.username == user.username).first()
        if db_user is None:
            new_user = models.User(username=user.username)
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            return dto.UserDTO(
                username=new_user.username
            )
        else:
            return dto.UserDTO(
                username=db_user.username
            )