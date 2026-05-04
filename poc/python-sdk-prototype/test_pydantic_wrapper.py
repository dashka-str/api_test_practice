from pydantic import BaseModel
from dataclasses import dataclass

@dataclass(frozen=True)
class ProcessInstanceKey:
    value: str

class MyModel(BaseModel):
    key: ProcessInstanceKey

try:
    # Simulating a JSON response from the API where the field is a string
    m = MyModel.model_validate({"key": "12345"})
    print("Success:", m)
    print("Dump:", m.model_dump())
except Exception as e:
    print("Error:", e)
