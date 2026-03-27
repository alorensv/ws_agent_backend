from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App General
    app_name: str = "WhatsApp Sales Agent V2"
    app_version: str = "2.5.0"
    
    # WhatsApp API
    wsp_verify_token: str
    wsp_phone_id: str
    wsp_token: str
    
    # Supabase (Database)
    supabase_url: str
    supabase_key: str
    
    # AI (DeepSeek / OpenAI)
    openai_api_key: str
    deepseek_api_base: str = "https://api.deepseek.com"
    
    # Redis (Cache / Workers)
    redis_url: str = "redis://redis:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="allow",
        case_sensitive=False
    )

settings = Settings()
