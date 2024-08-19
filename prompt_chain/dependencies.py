from prompt_chain.config import DB_URL
from prompt_chain.prompt_lib.db_manager import DatabaseManager


class DependencyManager:
    def __init__(self) -> None:
        self._db_manager: DatabaseManager | None = None

    @property
    def db_manager(self) -> DatabaseManager:
        if self._db_manager is None:
            self._db_manager = DatabaseManager(DB_URL)
        return self._db_manager
