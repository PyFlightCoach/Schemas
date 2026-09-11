from typing import Any

from pydantic import BaseModel


class CustomBaseModel(BaseModel):
    # Intercept the call and force exclude_defaults to True if not provided
    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        kwargs.setdefault("exclude_defaults", True)
        return super().model_dump(**kwargs)

    def model_dump_json(self, **kwargs: Any) -> str:
        kwargs.setdefault("exclude_defaults", True)
        return super().model_dump_json(**kwargs)