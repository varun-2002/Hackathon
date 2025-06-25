from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    SLACK_BOT_TOKEN: str
    SLACK_SIGNING_SECRET: str
    EINSTEIN_API_KEY: str
    
    class Config:
        env_file = ".env"

settings = Settings() 