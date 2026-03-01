from pydantic import BaseModel, Field


class SingleLevel(BaseModel):
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
