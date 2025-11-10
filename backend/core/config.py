from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    app_name: str = Field("BioCarta", alias="APP_NAME")
    base_url: str = Field("http://localhost:8080", alias="APP_BASE_URL")
    default_locale: str = Field("ru", alias="DEFAULT_LOCALE")
    jwt_secret: str = Field("change_me_to_a_long_random_string", alias="JWT_SECRET")
    jwt_alg: str = Field("HS256", alias="JWT_ALG")
    jwt_expires_min: int = Field(60*24*7, alias="JWT_EXPIRES_MIN")
    database_url: str = Field("sqlite:///./app.db", alias="DATABASE_URL")
    storage_dir: str = Field("./storage", alias="STORAGE_DIR")
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
