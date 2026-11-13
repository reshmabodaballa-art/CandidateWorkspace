
import json
from unittest.mock import Mock

import pytest
import requests

from src.ingestion.api_client import APIClient


def make_response(status_code, payload=None, headers=None):
    response = requests.Response()
    response.status_code = status_code
    response.headers.update(headers or {})
    response._content = json.dumps(
        payload or {"records": []}
    ).encode("utf-8")
    response.url = "http://localhost/mock-api/customers"
    return response


def test_rate_limit_429_retries_successfully(monkeypatch):
    monkeypatch.setattr(
        "src.ingestion.api_client.time.sleep",
        lambda delay: None
    )

    client = APIClient()

    client.session.get = Mock(side_effect=[
        make_response(429, headers={"Retry-After": "0"}),
        make_response(200, {"records": [{"id": 1}]})
    ])

    try:
        result = client.fetch_page("customers")

        assert result["records"][0]["id"] == 1
        assert client.session.get.call_count == 2
    finally:
        client.close()


def test_server_error_500_retries_successfully(monkeypatch):
    monkeypatch.setattr(
        "src.ingestion.api_client.time.sleep",
        lambda delay: None
    )

    client = APIClient()

    client.session.get = Mock(side_effect=[
        make_response(500),
        make_response(200, {"records": []})
    ])

    try:
        result = client.fetch_page("customers")

        assert result == {"records": []}
        assert client.session.get.call_count == 2
    finally:
        client.close()


def test_connection_error_retries_successfully(monkeypatch):
    monkeypatch.setattr(
        "src.ingestion.api_client.time.sleep",
        lambda delay: None
    )

    client = APIClient()

    client.session.get = Mock(side_effect=[
        requests.ConnectionError("Temporary connection failure"),
        make_response(200, {"records": []})
    ])

    try:
        result = client.fetch_page("customers")

        assert result == {"records": []}
        assert client.session.get.call_count == 2
    finally:
        client.close()


def test_unauthorized_error_does_not_retry(monkeypatch):
    client = APIClient()

    client.session.get = Mock(
        return_value=make_response(401)
    )

    try:
        with pytest.raises(requests.HTTPError):
            client.fetch_page("customers")

        assert client.session.get.call_count == 1
    finally:
        client.close()
