#!/usr/bin/python
# -*- coding: utf-8 -*-

# Generate SQS Messages in AWS using Boto3

## Import the SDK

import boto3
import datetime
import uuid

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


## Create the Queue
sqsQueue = create_SQS_queue('monitorPrinterPrice')

print(sqsQueue.url)
print(sqsQueue.attributes.get('DelaySeconds'))

## Sending SQS Messages
### Sending a message adds it to the end of the queue
msgData = {}
msgData['msgBody'] = "Howdy @ " + '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
msgData['msgAttributes'] = { 'Author' : { 'StringValue': 'Mystique', 'DataType': 'String' } }
send_SQS_msg(sqsQueue,msgData)

## Processing SQS Messages
process_SQS_queue(sqsQueue)