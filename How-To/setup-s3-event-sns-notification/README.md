# Amazon S3 Event Notifications
The Amazon S3 notification feature enables you to receive notifications when certain events happen in your bucket. 

![Amazon S3 Event Notifications](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-s3-event-sns-notification/images/AWS-S3-Events.png)

## Pre-Requisites for Configuring S3 Notifications
To enable notifications, you must,
1. First, Add a notification configuration(`SNS`) identifying the events you want Amazon S3 to publish,
   1. Update topic policy to allow S3 to publish messages(_Refer below for policy json code_)
   1. Subscribe to SNS with `email` notification
1. Second, Update the destinations where you want Amazon S3 to send the event notifications

### Granting Permissions for S3 to Publish Messages to an SNS Topic
IAM policy that needs to be attached to the destination SNS topic,

_**Note:** Dont forget to update to the `ARN` and `Bucketname` in the below policy_
```json
{
 "Version": "2008-10-17",
 "Id": "example-ID",
 "Statement": [
  {
   "Sid": "s3-event-notifier",
   "Effect": "Allow",
   "Principal": {
     "Service": "s3.amazonaws.com"
   },
   "Action": [
    "SNS:Publish"
   ],
   "Resource": "<UPDATE-YOUR-SNS-ARN-HERE>",
   "Condition": {
      "ArnLike": {          
      "aws:SourceArn": "arn:aws:s3:*:*:<UPDATE-YOUR-BUCKET-NAME-HERE>"
    }
   }
  }
 ]
}
