# Connect to S3 using boto

### Boto Installation
###### Ref [1] - https://boto3.readthedocs.io/en/latest/guide/quickstart.html#installation
```sh
pip install boto3
```

### Configure Boto
If you have the AWS CLI installed, then you can use it to configure your credentials file, By default, its location is at `~/.aws/credentials`
```sh
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
```

You may also want to set a default region. This can be done in the configuration file. By default, its location is at ~/.aws/config:
```sh
[default]
region=us-east-1
```
> Alternatively, you can pass a `region_name` when creating clients and resources.


### Precedence

Even if you have your boto config setup, you can also have credentials and options stored in environmental variables or you can explicitly pass them to method calls i.e.:
```sh
>>> boto.ec2.connect_to_region(
...     'us-west-2',
...     aws_access_key_id='foo',
...     aws_secret_access_key='bar')
```
In these cases where these options can be found in more than one place boto will first use the explicitly supplied arguments, if none found it will then look for them amidst environment variables and if that fails it will use the ones in boto config.

Thats it, Now you have setup boto to work with your AWS account. you can go ahead and use it.

For example, 

#### List all S3 your bucket names:
```sh
import boto3

# Let's use Amazon S3
s3 = boto3.resource('s3')

# Print out bucket names
for bucket in s3.buckets.all():
 print(bucket.name)
```
#### Upload a file to S3:
_This code assumes the file `test.jpg` exists in the current directory & the bucket `my-bucket-in-the-cloud` already exists
```sh
import boto3
s3 = boto3.resource('s3')
data = open('test.jpg', 'rb')
s3.Bucket('my-bucket-in-the-cloud').put_object(Key='test.jpg', Body=data)
```