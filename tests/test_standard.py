"""LangChain's standard tool tests (langchain-tests), offline: the client answers from a mock transport."""

from typing import Type

import pytest

pytest.importorskip("langchain_tests")

from langchain_tests.unit_tests import ToolsUnitTests  # noqa: E402

from langchain_witan import WitanErrorSearch  # noqa: E402
from tests.test_tools import client  # noqa: E402


class TestWitanErrorSearchStandard(ToolsUnitTests):
    @property
    def tool_constructor(self) -> Type[WitanErrorSearch]:
        return WitanErrorSearch

    @property
    def tool_constructor_params(self) -> dict:
        return {"client": client()}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"error": "npm error code ENEEDAUTH"}
