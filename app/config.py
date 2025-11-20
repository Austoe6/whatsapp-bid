from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    wa_access_token: str = Field(alias="WA_ACCESS_TOKEN")
    wa_phone_number_id: str = Field(alias="WA_PHONE_NUMBER_ID")
    wa_verify_token: str = Field(alias="WA_VERIFY_TOKEN")
    app_base_url: str = Field(alias="APP_BASE_URL")
    database_url: str = Field(default="sqlite:///./app.db", alias="DATABASE_URL")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()  # load at import time for simplicity
*** End Patch  ***!

