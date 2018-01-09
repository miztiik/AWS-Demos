# Configuring Amazon S3 Event Notifications


## Granting Permissions to Publish Messages to an SNS Topic
IAM policy that needs to be attached to the destination SNS topic,
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
```