from prompt_chain.config import DB_URL, OPENAI_API_KEY
from prompt_chain.prompt_lib.db_manager import DatabaseManager
from prompt_chain.prompt_lib.web_client import WebClient


class DependencyManager:
    def __init__(self) -> None:
        self._db_manager: DatabaseManager | None = None
        self._web_client: WebClient | None = None
        self._openai_api_key: str | None = OPENAI_API_KEY

    @property
    def db_manager(self) -> DatabaseManager:
        if self._db_manager is None:
            self._db_manager = DatabaseManager(DB_URL)
        return self._db_manager

    @property
    def web_client(self) -> WebClient:
        if self._web_client is None:
            self._web_client = WebClient()
        return self._web_client

    @property
    def openai_api_key(self) -> str:
        if self._openai_api_key is None:
            raise ValueError("OpenAI API key is not set")
        return self._openai_api_key
