import asyncio
import logging

from pyzeebe import ZeebeClient, ZeebeWorker, Job, create_insecure_channel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BPMN_FILE = "/home/dasha/practica/api-test-generator/path-analyser/fixtures/bpmn/service-task.bpmn"
PROCESS_ID = "Process_0zc9jbi"

async def main():
    logger.info("Setting up channel...")
    # NOTE: PyZeebe uses raw gRPC channels
    channel = create_insecure_channel(grpc_address="localhost:26500")
    
    client = ZeebeClient(channel)
    
    logger.info(f"Deploying BPMN from {BPMN_FILE}...")
    
    # Notice: we just pass the file path, no formal "Deployment" class to construct as in the REST API.
    await client.deploy_resource(BPMN_FILE)
    logger.info("BPMN deployed successfully!")

    # Setup Worker
    logger.info("Setting up worker for 'sampleJobType'...")
    worker = ZeebeWorker(channel)

    # Notice: Types are loosely bound by parameter names matching variable names in Zeebe.
    # A `job` parameter gives access to the raw Job object.
    @worker.task(task_type="sampleJobType")
    async def sample_job(job: Job, message: str = "default"):
        logger.info(f"Worker received job! Job Key: {job.key}, Process Instance Key: {job.process_instance_key}")
        logger.info(f"Incoming variable 'message': {message}")
        
        # We just return a dictionary to complete the job with variables.
        # No formal object representation for completions.
        return {"result": "success", "processedMessage": message.upper()}
    
    # Start worker in the background
    worker_task = asyncio.create_task(worker.work())

    # Create a process instance
    logger.info("Creating process instance...")
    
    # Notice: We pass variables as a plain dictionary. `run_process` returns the process instance key as an int (or tuple).
    instance_key = await client.run_process(bpmn_process_id=PROCESS_ID, variables={"message": "Hello from pyzeebe"})
    
    # Observe the type of instance_key - it's just an int! Very easy to accidentally mix up with a process_definition_key.
    logger.info(f"Created process instance with key: {instance_key} (Type: {type(instance_key).__name__})")

    # Give the worker a moment to poll and process the task
    await asyncio.sleep(3)
    
    logger.info("Stopping worker...")
    await worker.stop()
    await worker_task
    logger.info("Done.")
    
if __name__ == "__main__":
    asyncio.run(main())
