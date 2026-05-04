import httpx
from pydantic import BaseModel, ConfigDict
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from pathlib import Path

# ======================================================================
# Semantic Domain Types (Wrappers)
# We use dataclass(frozen=True) to prevent accidental coercion.
# For Pydantic to seamlessly serialize, we could add custom validators,
# but passing the raw string out via `.value` is typical in pure wrappers.
# ======================================================================

@dataclass(frozen=True)
class ProcessInstanceKey:
    value: str

    def __str__(self) -> str:
        # Prevent silent string coercion when formatting to JSON or logs
        # without explicit intent (optional, could just return self.value)
        return self.value

@dataclass(frozen=True)
class ProcessDefinitionKey:
    value: str

@dataclass(frozen=True)
class JobKey:
    value: str

@dataclass(frozen=True)
class DeploymentKey:
    value: str

@dataclass(frozen=True)
class TenantId:
    value: str

# ======================================================================
# REST DTOs representing Request/Response Bodies
# (Using pydantic BaseModel for automatic validation & easy dict export)
# ======================================================================

class CreateProcessInstanceRequest(BaseModel):
    processDefinitionKey: Optional[str] = None
    processDefinitionId: Optional[str] = None
    processDefinitionVersion: Optional[int] = None
    variables: Optional[Dict[str, Any]] = None
    tenantId: Optional[str] = None

class CreateProcessInstanceResponse(BaseModel):
    processDefinitionKey: str
    processDefinitionId: str
    processDefinitionVersion: int
    processInstanceKey: str
    tenantId: str

class ActivateJobsRequest(BaseModel):
    type: str
    maxJobsToActivate: int
    worker: str
    timeout: int
    fetchVariables: Optional[List[str]] = None
    tenantIds: Optional[List[str]] = None

class JobResponse(BaseModel):
    # Model configuration to allow arbitrary extra fields 
    # and map integers properly
    model_config = ConfigDict(extra='allow')
    
    jobKey: str
    type: str
    processInstanceKey: str
    processDefinitionKey: str
    processDefinitionVersion: int
    processDefinitionId: str
    worker: str
    retries: int
    deadline: int
    variables: Dict[str, Any]
    customHeaders: Dict[str, str]

class ActivateJobsResponse(BaseModel):
    jobs: List[JobResponse]

class CompleteJobRequest(BaseModel):
    variables: Optional[Dict[str, Any]] = None

class PublishMessageRequest(BaseModel):
    messageName: str
    correlationKey: Optional[str] = None
    timeToLive: Optional[int] = None
    messageId: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None
    tenantId: Optional[str] = None

class TopologyResponse(BaseModel):
    clusterSize: int
    partitionsCount: int
    replicationFactor: int
    gatewayVersion: str

@dataclass(frozen=True)
class DecisionDefinitionKey:
    value: str

class ModifyProcessInstanceRequest(BaseModel):
    instructions: List[Dict[str, Any]]

# ======================================================================
# Minimal Orchestration Cluster REST Client
# ======================================================================

class CamundaRestClient:
    """
    A typed wrapper around the Camunda 8 Orchestration Cluster REST API.
    Addresses limitations of untyped gRPC clients by strictly enforcing wrapper types,
    primarily for runtime boundaries and static checking.
    """
    def __init__(self, base_url: str = "http://localhost:8080/v2"):
        self.client = httpx.Client(base_url=base_url)

    def close(self):
        self.client.close()

    def deploy_resource(self, file_path: str, tenant_id: Optional[TenantId] = None) -> DeploymentKey:
        """POST /v2/deployments"""
        path = Path(file_path)
        files = {
            'resources': (path.name, open(path, 'rb'), 'application/octet-stream')
        }
        data = {}
        if tenant_id:
            data['tenantId'] = tenant_id.value
            
        resp = self.client.post("/deployments", data=data, files=files)
        resp.raise_for_status()
        json_body = resp.json()
        # Returning a strongly typed wrapper from the literal string
        return DeploymentKey(str(json_body.get('deploymentKey')))

    def create_process_instance(self, request: CreateProcessInstanceRequest) -> ProcessInstanceKey:
        """POST /v2/process-instances"""
        # exclude_none ensures we don't send nulls that might fail schema checks
        body = request.model_dump(exclude_none=True)
        resp = self.client.post("/process-instances", json=body)
        if resp.status_code >= 400:
            raise Exception(f"HTTP {resp.status_code}: {resp.text}")
        resp.raise_for_status()
        
        parsed = CreateProcessInstanceResponse.model_validate(resp.json())
        return ProcessInstanceKey(parsed.processInstanceKey)
        
    def search_instances(self, filter_query: Dict[str, Any]) -> Any:
        """POST /v2/process-instances/search"""
        # Very minimal stub for a search request
        resp = self.client.post("/process-instances/search", json=filter_query)
        resp.raise_for_status()
        return resp.json()

    def activate_jobs(self, request: ActivateJobsRequest) -> List[JobResponse]:
        """POST /v2/jobs/activation"""
        body = request.model_dump(exclude_none=True)
        resp = self.client.post("/jobs/activation", json=body)
        resp.raise_for_status()
        
        parsed = ActivateJobsResponse.model_validate(resp.json())
        return parsed.jobs

    def complete_job(self, job_key: JobKey, variables: Optional[Dict[str, Any]] = None) -> None:
        """POST /v2/jobs/{jobKey}/completion"""
        # Note the required usage of `.value` strictly isolates int-string leak
        endpoint = f"/jobs/{job_key.value}/completion"
        body = CompleteJobRequest(variables=variables).model_dump(exclude_none=True)
        
        resp = self.client.post(endpoint, json=body)
        resp.raise_for_status()

    def cancel_process_instance(self, process_instance_key: ProcessInstanceKey) -> None:
        """POST /v2/process-instances/{processInstanceKey}/cancellation"""
        endpoint = f"/process-instances/{process_instance_key.value}/cancellation"
        resp = self.client.post(endpoint, json={})
        resp.raise_for_status()

    def get_topology(self) -> TopologyResponse:
        """GET /v2/topology"""
        resp = self.client.get("/topology")
        resp.raise_for_status()
        return TopologyResponse.model_validate(resp.json())

    def publish_message(self, request: PublishMessageRequest) -> None:
        """POST /v2/messages/publication"""
        body = request.model_dump(exclude_none=True)
        resp = self.client.post("/messages/publication", json=body)
        resp.raise_for_status()

    def search_decisions(self, filter_query: Dict[str, Any]) -> Any:
        """POST /v2/decision-definitions/search"""
        resp = self.client.post("/decision-definitions/search", json=filter_query)
        resp.raise_for_status()
        return resp.json()

    def modify_process_instance(self, process_instance_key: ProcessInstanceKey, request: ModifyProcessInstanceRequest) -> None:
        """POST /v2/process-instances/{processInstanceKey}/modification"""
        endpoint = f"/process-instances/{process_instance_key.value}/modification"
        body = request.model_dump(exclude_none=True)
        resp = self.client.post(endpoint, json=body)
        resp.raise_for_status()

    def search_user_tasks(self, filter_query: Dict[str, Any]) -> Any:
        """POST /v2/user-tasks/search"""
        resp = self.client.post("/user-tasks/search", json=filter_query)
        resp.raise_for_status()
        return resp.json()

    def search_incidents(self, filter_query: Dict[str, Any]) -> Any:
        """POST /v2/incidents/search"""
        resp = self.client.post("/incidents/search", json=filter_query)
        resp.raise_for_status()
        return resp.json()
        
# Example usage block (won't run during import)
if __name__ == "__main__":
    client = CamundaRestClient()
    print("Client initialized")
    client.close()
