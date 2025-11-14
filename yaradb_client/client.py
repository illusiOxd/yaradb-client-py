import requests
import uuid
from typing import Any, Dict, List, Union


class YaraError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(f"Status code: {status_code}, Error: {message}")


class YaraConnectionError(YaraError):
    def __init__(self, host: str, original_error: Exception):
        super().__init__(f"Failed to connect to {host}. Is the server running? Error: {original_error}", None)


class YaraNotFoundError(YaraError):
    # Response 404
    pass


class YaraConflictError(YaraError):
    # Response 409
    pass


class YaraBadRequestError(YaraError):
    # Response 400
    pass


# --- Client ---

class YaraClient:
    def __init__(self, host: str = "http://127.0.0.1:8000"):
        self.host = host.rstrip('/')
        self.session = requests.Session()

    def _handle_response(self, response: requests.Response) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Handles HTTP response and raises exceptions on errors.
        Returns JSON data (dict or list) on success.
        """
        if response.status_code == 200:
            try:
                return response.json()
            except requests.JSONDecodeError:
                raise YaraError("Invalid JSON response from server", response.status_code)

        try:
            response_json = response.json()
            if isinstance(response_json, dict):
                error_detail = response_json.get("detail", "Unknown API error")
            else:
                error_detail = str(response_json)
        except requests.JSONDecodeError:
            error_detail = response.text or "Unknown API error"

        if response.status_code == 404:
            raise YaraNotFoundError(error_detail, 404)
        elif response.status_code == 409:
            raise YaraConflictError(error_detail, 409)
        elif response.status_code == 400:
            raise YaraBadRequestError(error_detail, 400)
        else:
            raise YaraError(error_detail, response.status_code)

    def ping(self) -> bool:
        try:
            response = self.session.get(f"{self.host}/ping", timeout=3)
            return response.status_code == 200 and response.json().get("status") == "alive"
        except requests.ConnectionError:
            return False
        except requests.Timeout:
            return False

    def create(self, name: str, body: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.host}/document/create"
        payload = {"name": name, "body": body}
        try:
            response = self.session.post(url, json=payload)
            return self._handle_response(response)  # type: ignore
        except requests.ConnectionError as e:
            raise YaraConnectionError(self.host, e)

    def get(self, doc_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
        url = f"{self.host}/document/get/{str(doc_id)}"
        try:
            response = self.session.get(url)
            return self._handle_response(response)  # type: ignore
        except requests.ConnectionError as e:
            raise YaraConnectionError(self.host, e)

    def find(self, filter_body: Dict[str, Any], include_archived: bool = False) -> List[Dict[str, Any]]:
        url = f"{self.host}/document/find"
        params = {"include_archived": include_archived}
        try:
            response = self.session.post(url, json=filter_body, params=params)
            return self._handle_response(response)  # type: ignore
        except requests.ConnectionError as e:
            raise YaraConnectionError(self.host, e)

    def update(self, doc_id: Union[str, uuid.UUID], version: int, body: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.host}/document/update/{str(doc_id)}"
        payload = {"version": version, "body": body}
        try:
            response = self.session.put(url, json=payload)
            return self._handle_response(response)  # type: ignore
        except requests.ConnectionError as e:
            raise YaraConnectionError(self.host, e)

    def archive(self, doc_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
        url = f"{self.host}/document/archive/{str(doc_id)}"
        try:
            response = self.session.put(url)
            return self._handle_response(response)  # type: ignore
        except requests.ConnectionError as e:
            raise YaraConnectionError(self.host, e)

    def combine(self, name: str, body: dict[str, Any], merge_strategy: str) -> Dict[str, Any]:
        url = f"{self.host}/document/combine"
        try:
            payload = {"name": name, "body": body, "merge_strategy": merge_strategy}
            response = self.session.post(url, json=payload)
            return self._handle_response(response) # type: ignore
        except requests.ConnectionError as e:
            raise YaraConnectionError(self.host, e)
