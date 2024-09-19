from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    username = Column(String, primary_key=True, index=True)

class Client(Base):
    __tablename__ = "clients"
    id = Column(String, primary_key=True, index=True)
    redirect_uri = Column(String)
    secret_hash = Column(String, nullable=True)
    jwks_url = Column(String, nullable=True)
    issuer = Column(String, nullable=True)

class ProductType(Base):
    __tablename__ = "product_types"
    urn = Column(String, primary_key=True, index=True)
    name = Column(String)

class Consent(Base):
    __tablename__ = "consents"
    id = Column(Integer, primary_key=True, index=True)
    user_username = Column(String, ForeignKey('users.username'))
    client_id = Column(String, ForeignKey('clients.id'))
    product_type_urn = Column(Integer, ForeignKey('product_types.urn'))
    product_id = Column(String)
    status = Column(String)

class ConsentHistory(Base):
    __tablename__ = "consent_history"
    id = Column(Integer, primary_key=True, index=True)
    user_username = Column(String, ForeignKey('users.username'))
    client_id = Column(String, ForeignKey('clients.id'))
    product_type_urn = Column(Integer, ForeignKey('product_types.urn'))
    product_id = Column(String)
    status = Column(String)
    datetime = Column(String)