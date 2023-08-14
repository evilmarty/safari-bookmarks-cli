from pydantic import BaseModel, Field
from typing import Annotated, Iterable, Literal, Union

ChildrenType = Annotated[
    Union["WebBookmarkTypeProxy", "WebBookmarkTypeLeaf", "WebBookmarkTypeList"],
    Field(discriminator="web_bookmark_type"),
]


class CloudKitSync(BaseModel, populate_by_name=True):
    cloud_kit_device_identifier: str = Field(alias="CloudKitDeviceIdentifier")
    cloud_kit_migration_state: int = Field(alias="CloudKitMigrationState")


class WebBookmarkType(BaseModel, extra="allow", populate_by_name=True):
    web_bookmark_uuid: str = Field(alias="WebBookmarkUUID")
    web_bookmark_type: str = Field(alias="WebBookmarkType")

    def __hash__(self) -> int:
        return hash(self.web_bookmark_uuid)


class WebBookmarkTypeProxy(WebBookmarkType):
    web_bookmark_type: Literal["WebBookmarkTypeProxy"] = Field(alias="WebBookmarkType", default="WebBookmarkTypeProxy")
    title: str = Field(alias="Title")


class WebBookmarkTypeLeaf(WebBookmarkType):
    web_bookmark_type: Literal["WebBookmarkTypeLeaf"] = Field(alias="WebBookmarkType", default="WebBookmarkTypeLeaf")
    url_string: str = Field(alias="URLString")
    uri_dictionary: dict[str, str] = Field(alias="URIDictionary", default_factory=dict)


class WebBookmarkTypeList(WebBookmarkType):
    web_bookmark_type: Literal["WebBookmarkTypeList"] = Field(alias="WebBookmarkType", default="WebBookmarkTypeList")
    title: str = Field(alias="Title")
    children: list[ChildrenType] = Field(alias="Children", default_factory=list)

    def __iter__(self) -> Iterable[WebBookmarkType]:
        return iter(self.children)

    def append(self, item: WebBookmarkType) -> None:
        self.children.append(item)

    def insert(self, index: int, item: WebBookmarkType) -> None:
        self.children.insert(index, item)

    def remove(self, item: WebBookmarkType) -> None:
        self.children.remove(item)
