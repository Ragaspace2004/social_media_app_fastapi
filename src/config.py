import os 
from dotenv import load_dotenv

load_dotenv()

class Settings:
    def __init__(self):
       #JWT 
       self.secret_key=self.get_required_env("SECRET_KEY")
       self.algorithm=self.get_required_env("ALGORITHM",default="HS256")
       self.token_expiration_minutes=self.get_int_env("TOKEN_EXPIRATION_MINUTES",default=30)
       
       # database
       self.database_url=self.get_required_env("DATABASE_URL")
       
       #security
       self.allowed_origins=self.get_list_env("ALLOWED_ORIGINS",default=["http://localhost:8000"])
       
    def get_required_env(self,key:str,default=None):
        value = os.getenv(key,default)
        if value is None:
           raise ValueError(f"{key} environment variable is required")
        return value
    
    def get_int_env(self,key:str,default=None):
        value = os.getenv(key)
        if value is None:
            if default is not None:
                return default
            raise ValueError(f"{key} environment variable is required")
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"{key} environment variable must be an integer")

    def get_list_env(self,key:str,default=None):
        value = os.getenv(key)  # Don't pass default here
        if value is None:
           return default if default is not None else []
        return [item.strip() for item in value.split(",")]
      
settings = Settings()