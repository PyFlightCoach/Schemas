from enum import Enum
from pydantic_core import CoreSchema, core_schema
from pydantic import GetCoreSchemaHandler
from typing import Any

##https://github.com/pydantic/pydantic/discussions/6466#discussioncomment-8219585
class EnumStr(float, Enum):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.any_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: x.name
            ),
        )

    @classmethod
    def validate(cls, v: Any):
        if isinstance(v, cls):
            return v
        elif isinstance(v, str):
            try:
                return cls[v]
            except KeyError:
                return None
#                raise ValueError(f"Invalid {cls.__name__}: {v}")
        else:
            raise ValueError(f"Unexpected type: {type(v)}")