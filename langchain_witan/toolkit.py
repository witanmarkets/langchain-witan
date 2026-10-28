from __future__ import annotations

from typing import List, Optional

from langchain_core.tools import BaseTool, BaseToolkit
from pydantic import ConfigDict, Field
from witan_sdk import Witan

from .tools import (
    WitanErrorSearch,
    WitanKnowledgeSearch,
    WitanListDatasets,
    WitanQueryDataset,
    WitanReadUnit,
)


class WitanToolkit(BaseToolkit):
    """The WITAN read tools, sharing one client.

    Without a key the toolkit holds the tools that work without one: error search, knowledge
    search, reading a free unit and listing datasets. With a key (``api_key=`` or ``WITAN_API_KEY``)
    it adds SQL over a dataset. No tool buys anything.

    Example:
        .. code-block:: python

            from langchain_witan import WitanToolkit

            tools = WitanToolkit().get_tools()
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: Witan = Field(default_factory=Witan)

    @classmethod
    def from_key(cls, api_key: Optional[str] = None, *, base_url: Optional[str] = None) -> "WitanToolkit":
        return cls(client=Witan(api_key, base_url=base_url))

    def get_tools(self) -> List[BaseTool]:
        tools: List[BaseTool] = [
            WitanErrorSearch(client=self.client),
            WitanKnowledgeSearch(client=self.client),
            WitanReadUnit(client=self.client),
            WitanListDatasets(client=self.client),
        ]
        if self.client.api_key:
            tools.append(WitanQueryDataset(client=self.client))
        return tools
