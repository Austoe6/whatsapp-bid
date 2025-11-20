from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Make non-critical settings optional to avoid import-time crashes on cold start.
    wa_access_token: str = Field(default="", alias="WA_ACCESS_TOKEN")
    wa_phone_number_id: str = Field(default="", alias="WA_PHONE_NUMBER_ID")
    wa_verify_token: str = Field(default="", alias="WA_VERIFY_TOKEN")
    app_base_url: str = Field(default="", alias="APP_BASE_URL")
    database_url: str = Field(default="sqlite:///./app.db", alias="DATABASE_URL")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()  # load at import time for simplicity