from enum import Enum
from typing import Optional
from pydantic import BaseModel

class ConsentTypeEnum(str, Enum):
    generic = 'generic'
    specific = 'specific'

class ConsentStatusEnum(str, Enum):
    revoked = 'revoked'
    granted = 'granted'

class UserDTO(BaseModel):
    username: Optional[str] = None

class ClientDTO(BaseModel):
    id: str
    redirect_uri: str

class ProductTypeDTO(BaseModel):
    urn: Optional[str] = None
    name: str

class ConsentDTO(BaseModel):
    key: str
    username: str
    client_id: str
    product_type_urn: str
    type: ConsentTypeEnum
    product_id: Optional[str] = None
    status: Optional[ConsentStatusEnum] = None

class ConsentHistoryDTO(ConsentDTO):
    datetime: str

class TokenDTO(BaseModel):
    type: str
    refresh_token: str
    access_token: str