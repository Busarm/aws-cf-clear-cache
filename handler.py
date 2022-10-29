import boto3
import time
import json

def run(event, context):
    if event is not None and len(event) >= 1:

        # If From Pipeline
        if val("CodePipeline.job", event) is not None:
            params = event["CodePipeline.job"]["data"]["actionConfiguration"][
                "configuration"]["UserParameters"]
            input = json.loads(params)
            pipeline = boto3.client("codepipeline")
            try:
                if invalidate_cache(val("distribution_id", input)):
                    return pipeline.put_job_success_result(
                        jobId=event["CodePipeline.job"]["id"])
                else:
                    return pipeline.put_job_failure_result(
                        jobId=event["CodePipeline.job"]["id"],
                        failureDetails={
                            "type": "JobFailed",
                            "message": "Failed to invalidate cache",
                            "externalExecutionId": "string",
                        },
                    )
            except Exception as e:
                return pipeline.put_job_failure_result(
                    jobId=event["CodePipeline.job"]["id"],
                    failureDetails={
                        "type": "JobFailed",
                        "message": str(e),
                    },
                )

        # If From Api Gateway
        elif val("queryParameters", event) is not None:
            input = val("queryParameters", event)
            if invalidate_cache(val("distribution_id", input)):
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "status": True,
                        "msg": "Successfuly Completed"
                    }),
                }
            else:
                raise ValueError("Expected 'distribution_id'.")

        elif val("body", event) is not None:
            input = val("body", event, True)
            if invalidate_cache(val("distribution_id", input)):
                return {
                    "statusCode": 200,
                    "body": json.dumps({
                        "status": True,
                        "msg": "Successfuly Completed"
                    }),
                }
            else:
                raise ValueError("Expected 'distribution_id'.")

        # If Raw
        else:
            input = event
            if invalidate_cache(val("distribution_id", input)):
                return {"status": True, "msg": "Successfuly Completed"}
            else:
                raise ValueError("Expected 'distribution_id'.")
    else:
        raise ValueError("Expected 'distribution_id'.")

def invalidate_cache(distribution_id):
    if distribution_id is not None:
        distribution_id = str(distribution_id).strip()
        try:
            allFiles = ["/*"]
            client = boto3.client("cloudfront")
            client.create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch={
                    "Paths": {
                        "Quantity": 1,
                        "Items": allFiles
                    },
                    "CallerReference": str(time.time()),
                },
            )
            return True
        except Exception as e:
            raise e
    else:
        return False


def val(name, data, default=None, isJson=False):
    """
    Get Environment Variable
    :name:
    """
    try:
        if isJson:
            return json.loads(data[name])
        else:
            return data[name]
    except:
        return default
