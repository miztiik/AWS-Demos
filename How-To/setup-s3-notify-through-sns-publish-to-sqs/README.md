# S3 Bucket Notification to SQS/SNS on Object Creation

```py
import boto3, json

REGION_NAME = "ap-south-1"
s3BucketName="trawler-urls-bucket"
ami_id=""

EC2_URL = "https://" + REGION_NAME + ".ec2.amazonaws.com"
AWS_AUTO_SCALING_URL = "https://autoscaling." + REGION_NAME +".amazonaws.com"


# email_address = user@example.com
sns_topic_name = "s3-object-created-" + s3BucketName.replace (" ", "_")
sqs_queue_name = "trawlerDataProcessor"
```

## Create the `S3` bucket
```py
s3_client = boto3.client('s3',REGION_NAME)
s3_client.create_bucket(Bucket= s3BucketName , CreateBucketConfiguration = { 'LocationConstraint': REGION_NAME })
```

## Lets create the SNS Topic
```py
sns_client = boto3.client('sns', REGION_NAME)
sns_topic_arn = sns_client.create_topic( Name = sns_topic_name)['TopicArn']
```


#### Setup S3 to publish to the SNS topic for activity in the specific S3 bucket.

##### Policy to allow S3 to publish to SNS Topic
```py
s3PubToSnsPolicy = {'Version': '2008-10-17',
                    'Id': 'Policy-S3-publish-to-sns', 'Statement': [{
    'Effect': 'Allow',
    'Principal': {'AWS': '*'},
    'Action': ['sns:Publish'],
    'Resource': sns_topic_arn,
    'Condition': {'ArnLike': {'aws:SourceArn': 'arn:aws:s3:*:*:'
                  + s3BucketName + ''}},
    }]}


sns_client.set_topic_attributes( TopicArn = sns_topic_arn , 
                                 AttributeName = "Policy" , 
                                 AttributeValue = json.dumps(s3PubToSnsPolicy)
                                )
```

### Set a nice little diplay name for the topic
```py
sns_client.set_topic_attributes( TopicArn = sns_topic_arn , 
                                 AttributeName = "DisplayName" , 
                                 AttributeValue = 'Urls2Crawl' 
                                )
```

#### Add a notification to the S3 bucket so that it sends messages to the SNS topic when objects are created (or updated)
```py
bucket_notifications_configuration = { 
    "TopicConfiguration" : { 
        "Events" : [ "s3:ObjectCreated:*" ], 
        "Topic" : sns_topic_arn 
        }
    }
    
s3_client.put_bucket_notification( Bucket = s3BucketName,
                                   NotificationConfiguration = bucket_notifications_configuration )
```
### Subscribe to the SNS Topic for EMail Notification
```py
sns_client.subscribe( TopicArn = sns_topic_arn , Protocol = "email", Endpoint="SOMEUSER@gmail.com" )
```


###### The above example connects an SNS topic to the S3 bucket notification configuration. Amazon also supports having the bucket notifications go directly to an SQS queue, but I do not recommend it.

######  Instead, send the S3 bucket notification to SNS and have SNS forward it to SQS.

###### This way, you can easily add other listeners to the SNS topic as desired. You can even have multiple SQS queues subscribed, which is not possible when using a direct notification configuration.

### Create the SQS queue 
```py
sqs_client = boto3.client('sqs', REGION_NAME)
```

#### Set permissions to allow SNS topic to post to the SQS queue
```py
sqs_policy = {
    "Version":"2012-10-17",
    "Statement":[
      {
        "Effect" : "Allow",
        "Principal" : { "AWS": "*" },
        "Action" : "sqs:SendMessage",
        "Resource" : sqs_queue_arn,
        "Condition" : {
          "ArnEquals" : {
            "aws:SourceArn" : sns_topic_arn
          }
        }
      }
    ]
}


sqs_attributes = {  'DelaySeconds':'3',
                    'ReceiveMessageWaitTimeSeconds' : '20',
                    'VisibilityTimeout' : '300',
                    'MessageRetentionPeriod':'86400',
                    'Policy' : json.dumps(sqs_policy)
                }

resp = sqs_client.create_queue( QueueName = sqs_queue_name, Attributes = sqs_attributes )
sqs_queue_url = resp['QueueUrl']
```

#### Get SQS Queue Attributes
```py
resp = sqs_client.get_queue_attributes( QueueUrl = sqs_queue_url, AttributeNames=[ 'QueueArn' ] )
sqs_queue_arn = resp['Attributes']['QueueArn']
```

## Subscribe the SQS queue to the SNS topic.
```py
sns_client.subscribe(
    TopicArn = sns_topic_arn,
    Protocol = "sqs",
    Endpoint = sqs_queue_arn
)
```

### Test SNS publishing to SQS
##### Upload test file to the S3 bucket, which will now generate both the email and a message to the SQS queue.
```py
# aws s3 cp [SOMEFILE] s3://$s3_bucket_name/testfile-02

s3Up = boto3.resource('s3')
s3Up.meta.client.upload_file('SOME_FILE.TXT', s3BucketName, 'hello.txt')
```

  """
  Function to clean up all the resources
  """
 ```py
 def cleanAll(resourcesDict=None):

    # Delete S3 Bucket    
    ### All of the keys in a bucket must be deleted before the bucket itself can be deleted:
    
    bucket = s3.Bucket( s3BucketName )
    
    for key in bucket.objects.all():
        key.delete()
    bucket.delete()
    
    # Delete SNS Topic
    sns_client.delete_topic( TopicArn = sns_topic_arn)

    # Delete SQS Topic
    sqs_client.delete_queue( QueueUrl = sqs_queue_url)
```
#### Ref [1] : https://alestic.com/2014/12/s3-bucket-notification-to-sqssns-on-object-creation/