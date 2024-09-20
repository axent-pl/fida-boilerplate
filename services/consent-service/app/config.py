from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CS_CODE_DB_ORIGIN: str = 'redis://localhost:6379'
    CS_CODE_LENGTH: int = 32
    CS_CODE_TTL_SECONDS: int = 30
    CD_CODE_NAMESPACE: str = 'authcode'

    CS_SESSION_DB_ORIGIN: str = 'redis://localhost:6379'
    CS_SESSION_SECRET: str = 'some-secret-???'
    
    CS_DB_URL: str = 'sqlite:///./test.db'
    

settings = Settings()