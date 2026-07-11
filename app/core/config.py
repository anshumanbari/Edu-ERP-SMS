from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str
    app_version: str

    database_host: str
    database_port: int
    database_name: str
    database_user: str
    database_password: str

    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    @property
    def database_url(self):
        return (
            f"postgresql+psycopg://"
            f"{self.database_user}:{self.database_password}"
            f"@{self.database_host}:{self.database_port}"
            f"/{self.database_name}"
        )

    class Config:
        env_file = ".env"


settings = Settings()