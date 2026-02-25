from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings


class ThreeLevels(BaseSettings):
    integer_with_default: int = Field(
        default=1,
        examples=[2, 3, 4],
        title="Integer setting with default",
        description="This is an integer setting with a default",
    )

    integer_no_default: int = Field(
        examples=[2, 3, 4],
        title="Integer setting without default",
        description="This is an integer setting without a default",
    )

    second_level: SecondLevel = Field(
        title="Second level setting",
        description="This is the second level setting",
    )


class SecondLevel(BaseSettings):
    list_with_default: list[int] = Field(
        default=[1, 2, 3],
        examples=[[2, 3, 4]],
        title="Integer setting with default",
        description="This is an integer setting with a default",
    )

    integer_no_default: list[int] = Field(
        examples=[[2, 3, 4]],
        title="Integer setting without default",
        description="This is an integer setting without a default",
    )

    third_level: ThirdLevel = Field(
        title="Third level setting",
        description="This is the third level setting",
    )

class ThirdLevel(BaseSettings):
    list_with_default: list[int] = Field(
        default=[1, 2, 3],
        examples=[[2, 3, 4]],
        title="Integer setting with default",
        description="This is an integer setting with a default",
    )

    integer_no_default: list[int] = Field(
        examples=[[2, 3, 4]],
        title="Integer setting without default",
        description="This is an integer setting without a default",
    )

ThreeLevels.model_rebuild()
SecondLevel.model_rebuild()