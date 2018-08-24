# Setup Amazon Elasticsearch Service Manual Index Snapshots

Snapshots are backups of a cluster's data and state. State includes cluster settings, node information, index settings, and shard allocation. Elasticsearch snapshots are incremental, meaning that they only store data that has changed since the last successful snapshot. This incremental nature means that the difference in disk usage between frequent and infreqent snapshots is often minimal.

Snapshots provide a convenient way to migrate data across Amazon Elasticsearch Service domains and recover from failure. You cannot use automated snapshots to migrate to new domains. Automated snapshots are read-only from within a given domain. For migrations, you must use manual snapshots.

Follow this article in **[Youtube](https://www.youtube.com/channel/UC_evcfxhjjui5hChhLE08tQ/playlists)**

![es-manual-snaps](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-manual-elasticsearch-snapshots/images/ElasticSearch-Manual-Snapshots-00.png)

### Prerequisites
You can generate a pre-signed URL programmatically, We will be using python SDK. Here are the high level steps
1. ElasticSearch Domain - [Get help here](https://youtu.be/cahU_A4c-eE)
1. Create S3 Bucket - `my-manual-es-snaps-bkt-010`
   - Get the Bucket ARN - `arn:aws:s3:::my-manual-es-snaps-bkt-001`
1. IAM Role: `my-manual-es-snap-creator-role` - [Get help here](https://www.youtube.com/watch?v=5g0Cuq-qKA0&index=11&list=PLxzKY3wu0_FLaF9Xzpyd9p4zRCikkD9lE)
    - Attach the following permissions, _Make sure to change the bucket ARNs_
    ```json
     {
       "Version": "2012-10-17",
       "Statement": [{
           "Action": [
             "s3:ListBucket"
           ],
           "Effect": "Allow",
           "Resource": [
             "arn:aws:s3:::my-manual-es-snaps-bkt-001"
           ]
         },
         {
           "Action": [
             "s3:GetObject",
             "s3:PutObject",
             "s3:DeleteObject"
           ],
           "Effect": "Allow",
           "Resource": [
             "arn:aws:s3:::my-manual-es-snaps-bkt-001/*"
           ]
         }
       ]
     }
    ```
    - Attach the following trust relationship to the role
    ```json
     {
       "Version": "2012-10-17",
       "Statement": [{
         "Sid": "",
         "Effect": "Allow",
         "Principal": {
           "Service": "es.amazonaws.com"
         },
         "Action": "sts:AssumeRole"
       }]
     }
    ```
1. IAM User with AWS CLI - `my-manual-es-snap-creator-user` [Get help here](https://www.youtube.com/watch?v=5g0Cuq-qKA0&list=PLxzKY3wu0_FLaF9Xzpyd9p4zRCikkD9lE&index=11)
   - Attach the following policy to the user
   ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Action": "iam:PassRole",
          "Resource": "arn:aws:iam::YOUR-ACCOUNT-ID:role/my-manual-es-snap-creator-role"
        },
        {
          "Effect": "Allow",
          "Action": "es:ESHttpPut",
          "Resource": "arn:aws:es:region:YOUR-ACCOUNT-ID:domain/YOU-ELASTIC-SEARCH-DOMAIN-NAME/*"
        }
      ]
    }
   ```

### Registering a Manual Snapshot Repository
You must register a snapshot repository with Amazon Elasticsearch Service before you can take manual index snapshots.
_If your ES domain resides within a VPC, your computer must be connected to the VPC in order for the request to successfully register the snapshot repository_

#### Prepare the EC2 Client to register our S3 Repo
**NOTE:** Change the `host`, `region` and the `ROLE ARN` in the below code to suit your environment.
```sh
# Install some prerequisites packages
yum -y install python-pip
pip install requests-aws4auth

# Create the pythong file to register the repo
cat >/tmp/register-repo.py <<"EOF"
import boto3
import requests
from requests_aws4auth import AWS4Auth

host = 'https://search-es-flowlogs-a1b2c3r4etc.eu-central-1.es.amazonaws.com/' # For example, search-my-domain.region.es.amazonaws.com
region = 'eu-central-1' # For example, us-west-1
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

# Register repository
path = '_snapshot/my-snapshot-repo' # the Elasticsearch API endpoint
url = host + path

payload = {
  "type": "s3",
  "settings": {
    "bucket": "my-manual-es-snaps-bkt-010",
    "region": "eu-central-1",
    "role_arn": "arn:aws:iam::YOUR-ACCOUNT-ID:role/my-manual-es-snap-creator-role"
  }
}

headers = {"Content-Type": "application/json"}

r = requests.put(url, auth=awsauth, json=payload, headers=headers)

print(r.status_code)
print(r.text)
EOF

# Execute the file to register repo
echo "============Going to register Repo=============="
chmod 700 /tmp/register-repo.py
python /tmp/register-repo.py
```
Output should be something like this,
```sh
200
{"acknowledged":true}
```

## Taking Manual Snapshots
You specify two pieces of information when you create a snapshot:
- Name of your snapshot repository
- Name for the snapshot
**Note:** _Snapshots are not instantaneous; they take some time to complete._
```sh
#curl -XPUT 'elasticsearch-domain-endpoint/_snapshot/repository/snapshot-name'

curl -XPUT 'https://search-es-flowlogs-gk3t6bxsrjb2zicwouomnxhk7u.eu-central-1.es.amazonaws.com/_snapshot/my-snapshot-repo/2018-08-12'
```
Use the following command to verify the state of snapshots of your domain:
```sh
curl -XGET 'https://search-es-flowlogs-gk3t6bxsrjb2zicwouomnxhk7u.eu-central-1.es.amazonaws.com/_snapshot/my-snapshot-repo/_all?pretty'
```

Output,
![es-manual-snaps](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-manual-elasticsearch-snapshots/images/ElasticSearch-Manual-Snapshots-04.png)

##### References
[1] - [AWS Docs - Working with Amazon Elasticsearch Service Index Snapshots](https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/es-managedomains-snapshots.html#es-managedomains-snapshot-registerdirectory)

[2] - [Boto Docs - Generating Presigned URLs](https://boto3.readthedocs.io/en/latest/guide/s3.html#generating-presigned-urls)