from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""
    whatsapp_app_secret: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    business_name: str = "Webora"
    graph_api_version: str = "v21.0"


settings = Settings()
