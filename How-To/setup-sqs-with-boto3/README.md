# Generate SQS Messages in AWS using Boto3

This tutorial covers how to,
 - Create a new queue, 
 - Get and use an existing queue,
 - Push new messages onto the queue, 
 - Finally, process messages from the queue by using _Resources_ and _Collections_.

### Import the SDK
```py
import boto3
import uuid
```

## Creating a Queue
Queues are created with a name. You may also optionally set queue attributes, such as the number of seconds to wait before an item may be processed. T

```py
# Get the service resource
sqsClient = boto3.resource('sqs')

"""
Function to create the sqs queue and return the queue ARN as return argument
@param {String} - Queue name as string
"""
def create_SQS_queue(SQS_QUEUE_NAME):
    # Set the SQS Queue Name
    # SQS_QUEUE_NAME = 'monitorPrinterPrice'

    # Create the queue, raise exception if unable to create queue
    try:
        # queueNameChk = sqsClient.get_queue_by_name(QueueName = SQS_QUEUE_NAME )
        # queueNameChk = queueNameChk.attributes['QueueArn'].split(':')[-1]
        queue = sqsClient.create_queue( 
            QueueName = SQS_QUEUE_NAME, 
            Attributes = { 
                'DelaySeconds':'15',
                'MaximumMessageSize':'262144',
                'VisibilityTimeout':'3600',
                'MessageRetentionPeriod':'86400'
            }     
        )
        # This returns an SQS Queue instance
        return queue
        raise
    except:
        print("Unable to create a SQS queue with the given name, recheck the queue name")

```
Our function `create_SQS_queue` is ready for use, Lets create a queue. The example use the queue name '_monitorPrinterPrice_'.

> _**Note:** The code above may throw an exception if you already have a queue named 'monitorPrinterPrice'._
```py
sqsQueue = create_SQS_queue('monitorPrinterPrice')        
```

## Using an Existing Queue
You can now access identifiers and attributes of our queue _monitorPrinterPrice_ through the Boto SQS Queue Resource `sqsQueue` as shown below,
```py
print(sqsQueue.url)
print(sqsQueue.attributes.get('DelaySeconds'))
```
The above code will print out:
```py
https://queue.amazonaws.com/532553517346/monitorPrinterPrice
15
```

#### Print out each queue name, which is part of its ARN
```py
for queue in sqs.queues.all():
    print(queue.attributes['QueueArn'].split(':')[-1])
```

## Sending SQS Messages
Sending a message adds it to the end of the queue.
```py
"""
Function to send messages to the given SQS queue
@param {BOTO Resource Type SQS Queue} - SQS Queue
#param {dict} - Python dictionary object with keys 'msgBody' & 'msgAttributes'
"""
def send_SQS_msg(sqsQueue, msgData):
    if msgData:
        response = sqsQueue.send_message( MessageBody = msgData['msgBody'], MessageAttributes = msgData['msgAttributes'] )

        # Print out any failures
        print("Number of failed Messages: %s" % response.get('Failed'))
```     

Now that we have defined our `send_SQS_msg` function, we can send messages like shown below,
```py
msgData = {}
msgData['msgBody'] = "Howdy @ " + '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
msgData['msgAttributes'] = { 'Author' : { 'StringValue': 'Mystique', 'DataType': 'String' } }
send_SQS_msg(sqsQueue,msgData)
```
The above code will print out:
```py
Number of failed Messages: None
```

## Process SQS Messages
Messages are processed in batches. Retrieves one or more messages, with a maximum limit of 10 messages, from the specified queue. 

For each message returned, the response includes the following:
 - Message body
 - MD5 digest of the message body.
 - Message ID you received when you sent the message to the queue.
 - Receipt handle.
 - Message attributes.
 - MD5 digest of the message attributes.

 Tt is likely you will get fewer or no messages than you requested per `ReceiveMessage` call. If the number of messages in the queue is extremely small; in which case you should repeat the request.

```py
"""
Function to process messages in the given SQS Queue
@param {BOTO Resource Type SQS Queue} - SQS Queue
"""
def process_SQS_queue(sqsQueue):
    # Process messages by printing out body and optional author name
    for message in sqsQueue.receive_messages(MessageAttributeNames=['Author']):
        # Get the custom author message attribute if it was set
        author_text = ''
        if message.message_attributes is not None:
            author_name = message.message_attributes.get('Author').get('StringValue')
            if author_name:
                author_text = ' ({0})'.format(author_name)
    
        # Print out the body and author (if set)
        print('Hi, {0}!{1}'.format(message.body, author_text))
    
        # Let the queue know that the message is processed
        print("Deleting message with ID : {0}".format(message.message_id))
        message.delete()
```

Lets call our new SQS processing function `process_SQS_queue`,
```py
process_SQS_queue(sqsQueue)
```
The above code will print out:
```py
Hi, Howdy @ 2016-09-28 19:46:24! (Mystique)
Deleting message with ID : 5a09803d-aebf-4e02-844a-e19e37029d20
```