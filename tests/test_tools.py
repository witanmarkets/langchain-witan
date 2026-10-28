import json

import httpx
from witan_sdk import Witan

from langchain_witan import (
    WitanErrorSearch,
    WitanKnowledgeSearch,
    WitanListDatasets,
    WitanQueryDataset,
    WitanReadUnit,
    WitanToolkit,
)

UNIT = "520553a6-be59-43dd-9f38-ece49c024b2c"


def handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/search/error":
        body = json.loads(request.content)
        assert body["error"].startswith("npm error code ENEEDAUTH")
        return httpx.Response(200, json={"signature": "npm error code ENEEDAUTH", "mode": "keyword",
                                         "results": [{"id": UNIT, "title": "npm Trusted Publishing fails"}]})
    if path == "/search":
        assert request.url.params["q"] == "github rate limit"
        return httpx.Response(200, json={"mode": "keyword", "results": [{"id": UNIT}]})
    if path == f"/knowledge/{UNIT}/full":
        return httpx.Response(200, json={"id": UNIT, "body": "x" * 20_000})
    if path == "/knowledge/paid/full":
        return httpx.Response(402, json={"error": "payment required: 0.05 USDC", "pay": "https://witan.markets/paid/knowledge/paid"})
    if path == "/projects":
        return httpx.Response(200, json={"projects": [{"slug": "mcp-server-liveness"}]})
    if path == "/projects/mcp-server-liveness/query":
        assert request.headers["authorization"] == "Bearer km_test"
        return httpx.Response(200, json={"columns": ["n"], "rows": [[3]], "count": 1})
    return httpx.Response(404, json={"error": "not found"})


def client(key: str | None = None) -> Witan:
    return Witan(key, base_url="https://witan.test", transport=httpx.MockTransport(handler), retries=0)


def test_toolkit_without_key_has_the_keyless_tools():
    names = [t.name for t in WitanToolkit(client=client()).get_tools()]
    assert names == ["witan_error_search", "witan_knowledge_search", "witan_read_unit", "witan_list_datasets"]


def test_toolkit_with_key_adds_sql():
    names = [t.name for t in WitanToolkit(client=client("km_test")).get_tools()]
    assert names[-1] == "witan_query_dataset"


def test_error_search_returns_signature_and_results():
    out = json.loads(WitanErrorSearch(client=client()).invoke({"error": "npm error code ENEEDAUTH\n at x"}))
    assert out["signature"] == "npm error code ENEEDAUTH"
    assert out["results"][0]["id"] == UNIT


def test_knowledge_search():
    out = json.loads(WitanKnowledgeSearch(client=client()).invoke({"query": "github rate limit"}))
    assert out["results"][0]["id"] == UNIT


def test_read_cuts_long_results_and_says_so():
    out = WitanReadUnit(client=client()).invoke({"unit_id": UNIT})
    assert out.endswith("[cut at 12000 characters]")


def test_priced_unit_is_not_bought_and_the_agent_is_told():
    out = WitanReadUnit(client=client()).invoke({"unit_id": "paid"})
    assert "these tools never buy" in out


def test_list_and_query_datasets():
    assert json.loads(WitanListDatasets(client=client()).invoke({}))[0]["slug"] == "mcp-server-liveness"
    out = json.loads(WitanQueryDataset(client=client("km_test")).invoke(
        {"slug": "mcp-server-liveness", "sql": "SELECT count(*) AS n FROM records"}))
    assert out["rows"] == [[3]]


def test_no_tool_buys():
    for tool in WitanToolkit(client=client("km_test")).get_tools():
        assert "buy" not in tool.name
