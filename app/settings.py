from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_user: str = "postgres"
    db_password: SecretStr = SecretStr("mysecretpassword")
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "library_db"

    max_book_count: int = 5

    @property
    def db_uri(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password.get_secret_value()}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def migration_uri(self):
        # use sync connection
        return f"postgresql://{self.db_user}:{self.db_password.get_secret_value()}@{self.db_host}:{self.db_port}/{self.db_name}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
