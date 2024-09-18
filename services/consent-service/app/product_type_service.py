from fastapi import Depends
from sqlalchemy.orm import Session

import app.components as components
import app.dto as dto
import app.models as models

class ProductTypeService:

    def __init__(self, db: Session = Depends(components.get_db)):
        self.db: Session = db


    def upsert_product_type(self, product_type: dto.ProductTypeDTO) -> dto.ProductTypeDTO:
        db_product_type = self.db.query(models.ProductType).filter(models.ProductType.urn == product_type.urn).first()
        if db_product_type is None:
            new_product_type = models.ProductType(urn=product_type.urn, name=product_type.name)
            self.db.add(new_product_type)
            self.db.commit()
            self.db.refresh(new_product_type)
            return dto.ProductTypeDTO(
                urn=new_product_type.urn,
                name=new_product_type.name
            )
        else:
            db_product_type.name = product_type.name
            self.db.commit()
            self.db.refresh(db_product_type)
            return dto.ProductTypeDTO(
                urn=db_product_type.urn,
                name=db_product_type.name
            )