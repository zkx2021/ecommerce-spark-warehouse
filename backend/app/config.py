import os
from dataclasses import dataclass


@dataclass(frozen=True)
class MySqlSettings:
    host: str
    port: int
    database: str
    user: str
    password: str

    @classmethod
    def from_env(cls) -> "MySqlSettings":
        return cls(
            host=os.getenv("ADS_MYSQL_HOST", "localhost"),
            port=int(os.getenv("ADS_MYSQL_PORT", "3306")),
            database=os.getenv("ADS_MYSQL_DATABASE", "ecommerce_ads"),
            user=os.getenv("ADS_MYSQL_USER", "ecommerce"),
            password=os.getenv("ADS_MYSQL_PASSWORD", "ecommerce_password"),
        )
