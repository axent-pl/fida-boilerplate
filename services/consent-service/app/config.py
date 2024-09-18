from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CS_CODE_DB_ORIGIN: str = 'redis://localhost:6379'
    CS_SESSION_DB_ORIGIN: str = 'redis://localhost:6379'
    CS_DB_URL: str = 'sqlite:///./test.db'
    CS_SESSION_SECRET: str = 'some-secret-???'

settings = Settings()