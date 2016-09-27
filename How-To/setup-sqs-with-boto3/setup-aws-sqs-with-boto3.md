# Generate SQS Messages in AWS using Boto3

This tutorial covers how to,
 - Create a new queue, 
 - Get and use an existing queue,
 - Push new messages onto the queue, 
 - Finally, process messages from the queue by using _Resources_ and _Collections_.

## Import the SDK
```sh
import boto3
import uuid
```

## Creating a Queue
Queues are created with a name. You may also optionally set queue attributes, such as the number of seconds to wait before an item may be processed. The examples below will use the queue name '_printerPriceWatch_'. Before creating a queue, you must first get the SQS service resource:

> _**Note:** The code above may throw an exception if you already have a queue named 'printerPriceWatch'._

```sh
# Get the service resource
sqs_client = boto3.resource('sqs')

# Create the queue. This returns an SQS.Queue instance
queue = sqs_client.create( QueueName = 'printerPriceWatch', Attributes = { 'DelaySeconds':'5' } )

# You can now access identifiers and attributes
print(queue.url)
print(queue.attributes.get('DelaySeconds'))
```
