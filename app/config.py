from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_hostname: str  # Corrected from databse_hostname
    database_port: str
    database_password: str
    database_name: str
    database_username: str  # Corrected from databse_usernmae
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    
    
    # This configures the settings to read from .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()

