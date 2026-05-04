from camunda_rest_client import (
    CamundaRestClient,
    CreateProcessInstanceRequest,
    ActivateJobsRequest,
    JobKey,
    ProcessInstanceKey
)
import time
import httpx

BPMN_FILE = "/home/dasha/practica/api-test-generator/path-analyser/fixtures/bpmn/service-task.bpmn"
PROCESS_ID = "Process_0zc9jbi"

def run_example():
    client = CamundaRestClient(base_url="http://localhost:8080/v2")
    try:
        # 1. Deploy Process
        print(f"Deploying {BPMN_FILE}...")
        deploy_key = client.deploy_resource(BPMN_FILE)
        print(f"Deployed with key: {deploy_key.value} (Type: {type(deploy_key).__name__})")
        
        # 2. Create Process Instance
        print(f"Creating process instance for {PROCESS_ID}...")
        request = CreateProcessInstanceRequest(
            processDefinitionId=PROCESS_ID,
            variables={"message": "Hello from Python REST SDK"}
        )
        instance_key = client.create_process_instance(request)
        print(f"Created instance: {instance_key.value} (Type: {type(instance_key).__name__})")
        
        # 3. Activate Jobs
        print("Activating jobs for 'sampleJobType'...")
        job_request = ActivateJobsRequest(
            type="sampleJobType",
            maxJobsToActivate=1,
            worker="python-rest-worker",
            timeout=60000
        )
        jobs = client.activate_jobs(job_request)
        
        for job in jobs:
            print(f"Activated Job! Job Key: {job.jobKey}")
            # Wrap the string key in the domain type
            job_key = JobKey(job.jobKey)
            
            # 4. Complete Job
            print(f"Completing job {job_key.value}...")
            client.complete_job(
                job_key=job_key,
                variables={"result": "success", "echo": job.variables.get("message")}
            )
            print("Job completed!")
        
        print("Example finished successfully.")
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e}")
        print(f"Response body: {e.response.text}")
    except Exception as e:
        print(f"Exception occurred: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    run_example()
