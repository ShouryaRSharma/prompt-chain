from collections.abc import Mapping
from logging import Logger, getLogger
from typing import Any

import requests

logger: Logger = getLogger(__name__)


class WebClient:
    def __init__(self, timeout: int = 120):
        self.client: requests.Session = requests.Session()
        self._timeout: int = timeout

    def post(
        self, url: str, headers: Mapping[str, str], json: dict[str, Any] | None = None
    ) -> dict[str, Any] | Any:
        """
        Make a POST request to the specified URL.

        Args:
            url (str): The URL to send the POST request to.
            headers (Mapping[str, str]): The headers to include in the request.
            json (dict | None, optional): The JSON payload to send with the request. Defaults to None.

        Returns:
            dict[str, Any]: The JSON response from the server.

        Raises:
            requests.RequestException: If an error occurs during the request.
        """
        try:
            response: requests.Response = self.client.post(
                url, headers=headers, json=json, timeout=self._timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"An error occurred: {e}")
            raise

    def close(self) -> None:
        """Close the client session."""
        self.client.close()

    def __enter__(self) -> "WebClient":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        self.close()
