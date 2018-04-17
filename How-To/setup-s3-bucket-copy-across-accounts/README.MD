# Copy S3 Bucket Objects Across AWS Accounts

You can copy AWS S3 objects from one AWS account to another by using the S3 `COPY` operation. You must grant the destination AWS account access to the source AWS account's resources by using Amazon S3 `Access Control Lists (ACLs)` or `bucket policies`. 
![Copy S3 Bucket Objects Across AWS Accounts](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/img/setup-s3-bucket-copy-across-accounts.png)
### Step 1: Get the 12 digit number of the  `Destination AWS Account`
- **Sign in** to the AWS Management Console for the destination AWS account.
- In the navigation bar, click **Support**, and then click **Support Center**. The account number (for example, `222222222222`) is displayed in the upper-right corner of the Support Center.

### Step 2: Attach the policy to `Source S3 Bucket`
The Bucket policy set up in the source AWS account. _Do NOT forget to change the account number and bucket name in the below policy, otherwise it will not work_
###### For help on setting the ACL [check here](https://docs.aws.amazon.com/AmazonS3/latest/user-guide/set-permissions.html)
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DelegateS3Access",
            "Effect": "Allow",
            "Principal": {"AWS": "222222222222"},
            "Action": ["s3:ListBucket","s3:GetObject"],
            "Resource": [
                "arn:aws:s3:::YOUR-SOURCE-BUCKET-NAME-HERE/*",
                "arn:aws:s3:::YOUR-SOURCE-BUCKET-NAME-HERE"
            ]
        }
    ]
}
```

### Step 3: Attach a policy to a `IAM User` in the destination AWS account
Setup an IAM User in the destination account and attach this user policy to to delegate access to the bucket in the source AWS account.
```JSON
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:GetObject"
            ],
            "Resource": [
                "arn:aws:s3:::YOUR-SOURCE-BUCKET-NAME-HERE",
                "arn:aws:s3:::YOUR-SOURCE-BUCKET-NAME-HERE/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": [
                "arn:aws:s3:::YOUR-DESTINATION-BUCKET-NAME-HERE",
                "arn:aws:s3:::YOUR-DESTINATION-BUCKET-NAME-HERE/*"
            ]
        }
    ]
}
```

### Step 4: Sync S3 Objects To Destination
When the abovee steps are completed, the "destination" account can copy objects by using the AWS Command Line Interface (CLI) commands `cp` or `sync`.
_**Note:** Successful execution of the following command assumes that the AWS CLI has been correctly configured for the `IAM user`(in step 3) in the destination AWS account._

```sh
aws s3 sync s3://YOUR-SOURCE-BUCKET-NAME-HERE s3://YOUR-DESTINATION-BUCKET-NAME-HERE --source-region SOURCE-REGION-NAME --region DESTINATION-REGION-NAME

# For Example,
aws s3 sync s3://my-us-west-2-bucket s3://my-us-east-1-bucket --source-region us-west-2 --region us-east-1
```

