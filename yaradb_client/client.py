import requests
import uuid
from typing import Any, Dict, List, Union, Optional


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
        elif response.status_code == 422:
            raise YaraBadRequestError(f"Validation Error: {error_detail}", 422)
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

    # --- Document Operations ---

    def create(self, table_name: str, name: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a new document in the specified table.
        :param table_name: Name of the table (required in v3.0)
        :param name: Name of the document
        :param body: Document content
        """
        url = f"{self.host}/document/create"
        payload = {
            "table_name": table_name,
            "name": name,
            "body": body
        }
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

    def combine(self, document_ids: List[Union[str, uuid.UUID]], name: str, merge_strategy: str = "overwrite") -> Dict[str, Any]:
        url = f"{self.host}/document/combine"
        payload = {
            "name": name,
            "document_ids": [str(doc_id) for doc_id in document_ids],
            "merge_strategy": merge_strategy
        }
        try:
            response = self.session.post(url, json=payload)
            return self._handle_response(response)  # type: ignore
        except requests.ConnectionError as e:
            raise YaraConnectionError(self.host, e)

    # --- Table Operations (New in v3.0) ---

    def create_table(
        self,
        name: str,
        mode: str = "free",
        schema: Optional[Dict[str, Any]] = None,
        unique_fields: Optional[List[str]] = None,
        read_only: bool = False
    ) -> Dict[str, Any]:
        """
        Creates a new table with specific configuration.
        :param name: Table name
        :param mode: 'free' (schemaless) or 'strict' (enforces schema)
        :param schema: JSON Schema definition (required for strict mode)
        :param unique_fields: List of fields that must be unique
        :param read_only: If True, table accepts no writes
        """
        url = f"{self.host}/table/create"
        payload = {
            "name": name,
            "mode": mode,
            "read_only": read_only
        }
        if schema:
            payload["schema_definition"] = schema
        if unique_fields:
            payload["unique_fields"] = unique_fields

        try:
            response = self.session.post(url, json=payload)
            return self._handle_response(response)  # type: ignore
        except requests.ConnectionError as e:
            raise YaraConnectionError(self.host, e)

    def list_tables(self) -> List[Dict[str, Any]]:
        url = f"{self.host}/table/list"
        try:
            response = self.session.get(url)
            return self._handle_response(response)  # type: ignore
        except requests.ConnectionError as e:
            raise YaraConnectionError(self.host, e)

    def get_table(self, name: str) -> Dict[str, Any]:
        url = f"{self.host}/table/{name}"
        try:
            response = self.session.get(url)
            return self._handle_response(response)  # type: ignore
        except requests.ConnectionError as e:
            raise YaraConnectionError(self.host, e)

    def delete_table(self, name: str) -> Dict[str, Any]:
        url = f"{self.host}/table/{name}"
        try:
            response = self.session.delete(url)
            return self._handle_response(response)  # type: ignore
        except requests.ConnectionError as e:
            raise YaraConnectionError(self.host, e)

    def get_table_documents(self, name: str) -> List[Dict[str, Any]]:
        url = f"{self.host}/table/{name}/documents"
        try:
            response = self.session.get(url)
            return self._handle_response(response)  # type: ignore
        except requests.ConnectionError as e:
            raise YaraConnectionError(self.host, e)

    # --- System Operations ---

    def self_destruct(self, verification_phrase: str, safety_pin: int, confirm: bool = True) -> Dict[str, Any]:
        """
        Wipes all data from the database. USE WITH CAUTION.
        :param verification_phrase: Must be 'BDaray'
        :param safety_pin: Usually (Current Year + 1)
        """
        url = f"{self.host}/system/self-destruct"
        payload = {
            "verification_phrase": verification_phrase,
            "safety_pin": safety_pin,
            "confirm": confirm
        }
        try:
            response = self.session.request("DELETE", url, json=payload)
            return self._handle_response(response)  # type: ignore
        except requests.ConnectionError as e:
            raise YaraConnectionError(self.host, e)