from typing import Any

from backend.app.config import MySqlSettings


def connect_mysql(settings: MySqlSettings | None = None) -> Any:
    import mysql.connector

    resolved = settings or MySqlSettings.from_env()
    return mysql.connector.connect(
        host=resolved.host,
        port=resolved.port,
        database=resolved.database,
        user=resolved.user,
        password=resolved.password,
    )
