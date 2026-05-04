# Python SDK Automation Boundary

This document explicitly defines the boundary between what a machine (code generator) can automate and what requires human architectural judgment when emitting the Python Camunda REST SDK based on OpenAPI `x-semantic-type` annotations.

## 1. Human (Architect) Responsibilities: The "Once" Decisions
A machine cannot blindly intuit the idiomatic tradeoffs of a language's ecosystem. The human must define the template pattern and baseline logic for the generator.

* **Choosing the Paradigm:** The generator must be explicitly configured (via its template) to emit `@dataclass(frozen=True)` wrappers rather than `typing.NewType` or `str` subclasses. This is a human architectural choice based on the desired strictness-to-overhead ratio in Python.
* **Serialization Bridging:** True Python wrapper classes are serialized as nested dictionaries by default. To make HTTP payloads transparent (like unwrapped strings/ints) over the Wire, the human must template custom serialization hooks once. For example, providing the `__get_pydantic_core_schema__` boilerplate in the generator's template ensures the wrapper seamlessly maps to/from raw JSON strings and int primitives without breaking the Pydantic models.

## 2. Machine (Generator) Responsibilities: The "N-Times" Execution
Once the human provisions the base Python template logic and bridging boilerplate, the machine handles 100% of the scalable extraction, mapping, and propagation automatically based on the OpenAPI spec.

* **Extraction from the Spec:** The generator sweeps the bundled OpenAPI specification directly (specifically `spec/bundled/rest-api.bundle.json`), detects all `#/$defs` schemas, and identifies fields containing exactly `{"x-semantic-type": "..."}`. For example, upon inspecting `rest-api.bundle.json`, the `ProcessInstanceKey` schema and properties referencing it are marked with this tag. This ensures the output is 100% spec-driven rather than human-curated.
* **Emission of Domain Classes:** The generator programmatically outputs every unique wrapper class (e.g., `class ProcessInstanceKey`, `class DeploymentKey`) alongside the templated Pydantic lifecycle hooks so they behave correctly at runtime.
* **Property Mapping:** The generator walks paths, request bodies, and response classes, automatically replacing raw `str` or `int` typings with the properly detected wrapper class in the generated `pydantic.BaseModel` operation objects. No manual intervention is needed per-endpoint.