from pydantic import BaseModel, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic_core import core_schema
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ProcessInstanceKey:
    value: str

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        # Validate from string (or int) -> ProcessInstanceKey
        def validate(v: Any) -> "ProcessInstanceKey":
            if isinstance(v, cls):
                return v
            return cls(str(v))
        
        # Serialize back to string
        return core_schema.no_info_after_validator_function(
            validate,
            core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda wrapper: wrapper.value, 
                info_arg=False, 
                return_schema=core_schema.str_schema()
            )
        )

class MyModel(BaseModel):
    key: ProcessInstanceKey

m = MyModel.model_validate({"key": 12345}) # Testing int->str->Wrapper
print("Success instance:", m)
print("Dump dict:", m.model_dump())
print("Dump json:", m.model_dump_json())
