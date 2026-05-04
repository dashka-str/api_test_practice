"""
Drafting the wrapper class pattern for Domain semantic types (e.g. ProcessInstanceKey)
We evaluate three Python idioms:
1. typing.NewType (Zero runtime overhead, strict static isolation)
2. Custom class subclassing `str` (Allows implicit string coercion, but leaks string methods to domains)
3. @dataclass(frozen=True) wrapper (True domain encapsulation)
"""

from typing import NewType
from dataclasses import dataclass
from typing import Mapping, Any

# ======================================================================
# Pattern 1: typing.NewType
# Pros: Zero overhead, just a string at runtime.
# Cons: No ability to add methods. Cannot encapsulate value properly.
# ======================================================================
ProcessDefinitionKey_NT = NewType("ProcessDefinitionKey_NT", str)
ProcessInstanceKey_NT = NewType("ProcessInstanceKey_NT", str)

def run_process_nt(pd_key: ProcessDefinitionKey_NT) -> ProcessInstanceKey_NT:
    # At runtime, these are literally strings.
    return ProcessInstanceKey_NT(f"instance_of_{pd_key}")


# ======================================================================
# Pattern 2: Strong Wrapper Class (Dataclass)
# Pros: Complete isolation, prevents string operations natively, 
#       can add from_int / to_str methods. True "Wrapper Class".
# Cons: Requires extracting `.value` or casting `str(obj)` when dumping json.
# ======================================================================
@dataclass(frozen=True)
class ProcessInstanceKey:
    """Strong encapsulation preventing integer/string muddling."""
    value: str

    def __str__(self) -> str:
        return self.value

@dataclass(frozen=True)
class ProcessDefinitionKey:
    value: str

    def __str__(self) -> str:
        return self.value

def run_process_wrapper(pd_key: ProcessDefinitionKey) -> ProcessInstanceKey:
    return ProcessInstanceKey(f"instance_of_{pd_key.value}")


# ======================================================================
# Pattern 3: Subclassing str
# Pros: Acts like a string in serialization out of the box.
# Cons: Inherits string methods (e.g., key.upper()). Sometimes considered 
#       a code-smell because it breaks object equivalence logic.
# ======================================================================
class JobKey(str):
    pass

class VariableName(str):
    pass

def complete_job_subclass(job_key: JobKey, vars: Mapping[VariableName, Any]) -> None:
    pass

# ======================================================================
# MYPY VALIDATION TESTS
# ======================================================================
def type_safety_test():
    # 1. NewType catches mismatches
    pd_nt = ProcessDefinitionKey_NT("def123")
    pi_nt = ProcessInstanceKey_NT("inst456")
    
    # mypy ERROR: Argument 1 to ... has incompatible type
    run_process_nt(pi_nt)  
    
    # 2. Wrapper dataclass catches mismatches natively and at runtime (if we added isinstance checks)
    pd_wrap = ProcessDefinitionKey("def123")
    pi_wrap = ProcessInstanceKey("inst456")
    
    # mypy ERROR: Argument 1 to ... has incompatible type
    run_process_wrapper(pi_wrap) 
    
    # 3. String Inheritance catches mismatches
    jk = JobKey("job1")
    vn = VariableName("var_a")
    
    complete_job_subclass(vn, {}) # mypy ERROR

    # Behavior difference:
    print(f"NT: {pd_nt.upper()}") # Valid statically and at runtime
    print(f"Wrapper: {pd_wrap.value.upper()}") # Must explicitly access value
    # print(pd_wrap.upper()) # AttributeError natively, mypy ERROR statically
    print(f"Subclass: {jk.upper()}") # Valid statically and at runtime
