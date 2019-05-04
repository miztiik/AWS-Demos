# Setup Amazon Elasticsearch Service Manual Index Snapshots

Snapshots are backups of a cluster's data and state. State includes cluster settings, node information, index settings, and shard allocation. Elasticsearch snapshots are incremental, meaning that they only store data that has changed since the last successful snapshot. This incremental nature means that the difference in disk usage between frequent and infrequent snapshots is often minimal.

Snapshots provide a convenient way to migrate data across Amazon Elasticsearch Service domains and recover from failure. Automated snapshots are read-only from within a given domain. You cannot use automated snapshots to migrate to new domains. For migrations, you must use manual snapshots.

Follow this article in **[Youtube](https://www.youtube.com/channel/UC_evcfxhjjui5hChhLE08tQ/playlists)**

![es-manual-snaps](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-manual-elasticsearch-snapshots/images/ElasticSearch-Manual-Snapshots-00.png)

### Prerequisites
1. ElasticSearch Domain - [Get help here](https://youtu.be/cahU_A4c-eE)
1. Create S3 Bucket - `my-manual-es-snaps-bkt-001`
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
1. EC2 running Linux that can connect to the ES Cluster - _Simply host it in the same VPC/subnet as ES_
   1. AWS CLI Configured with IAM User `my-manual-es-snap-creator-role`

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

host = 'https://search-es-flowlogs-a1b2c3r4etc.eu-central-1.es.amazonaws.com/'
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
    "bucket": "my-manual-es-snaps-bkt-001",
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
- Name of your snapshot repository - Ex: `my-snapshot-repo`
- Name for the snapshot - Ex: `2018-08-24`

**Note:** _Snapshots are not instantaneous; they take some time to complete._
```sh
# curl -XPUT 'elasticsearch-domain-endpoint/_snapshot/repository/snapshot-name'

curl -XPUT 'https://search-es-flowlogs-a1b2c3r4etc.eu-central-1.es.amazonaws.com/_snapshot/my-snapshot-repo/2018-08-24'
```
Use the following command to verify the state of snapshots of your domain:
```sh
curl -XGET 'https://search-es-flowlogs-a1b2c3r4etc.eu-central-1.es.amazonaws.com/_snapshot/my-snapshot-repo/_all?pretty'
```

Output,
![es-manual-snaps](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-manual-elasticsearch-snapshots/images/ElasticSearch-Manual-Snapshots-04.png)

#### Back up an index
By default, Amazon ES snapshots the entire cluster’s indexes. By snapshotting a single index, you give yourself flexibility in where and when you restore the data. You can alter the default behavior with the `indices` setting.
```sh
curl -XPUT 'https://search-es-flowlogs-a1b2c3r4etc.eu-central-1.es.amazonaws.com/_snapshot/my-snapshot-repo/2018-08-24' 
-d'{
  "indices": "cwl-2018-07-16",
  "ignore_unavailable": true,
  "include_global_state": false
}'
```
You can specify one or more indexes for backup in this snapshot. You can choose to ignore errors if any of the indexes is not available by setting `ignore_unavailable` to false. You also might want to store the cluster's global state. However, for index-level backups, doing this usually won't make sense. Set `include_global_state` to `false`.

You can also use the `_snapshot` API action to check the status of your snapshot or get a list of all snapshots in the repository.

```sh
curl -XGET 'https://search-es-flowlogs-a1b2c3r4etc.eu-central-1.es.amazonaws.com/_snapshot/my-snapshot-repo/_status'
curl -XGET 'https://search-es-flowlogs-a1b2c3r4etc.eu-central-1.es.amazonaws.com/_snapshot/my-snapshot-repo/_all'
```
### Restoring Snapshots
To restore, you must ensure that the index is not open. This state is normally the case if you are reloading old data into the same cluster. If the index is open, delete the existing index first, then restore your backup.

When you restore, you specify the snapshot, and also any indexes that are in the snapshot. You do this in much the same way as when you took the snapshot in the first place.

The following example restores just one index, `cwl-2018-08-22`, from `2018-08-12` in the `my-snapshot-repo` snapshot repository:
```sh
curl -XPOST 'https://search-es-flowlogs-01-a1b2c3r4etc.eu-central-1.es.amazonaws.com/_snapshot/my-snapshot-repo/2018-08-24/_restore' -d'{
  "indices": "cwl-2018-08-22",
  "ignore_unavailable": false,
  "include_global_state": false
}' -H 'Content-Type: application/json'

# To restore two indices
curl -XPOST 'https://search-es-flowlogs-01-a1b2c3r4etc.eu-central-1.es.amazonaws.com/_snapshot/my-snapshot-repo/2018-08-24/_restore' -d'{
  "indices": "cwl-2018-08-22,cwl-2018-08-23",
  "ignore_unavailable": false,
  "include_global_state": false
}' -H 'Content-Type: application/json'

# To restore the entire snapshot
curl --XPUT 'https://search-es-flowlogs-01-a1b2c3r4etc.eu-central-1.es.amazonaws.com/_all'
```
### Deleting Indices
If you don't plan to restore all indices, though, you might want to delete only one:
```sh
curl -XDELETE 'https://search-es-flowlogs-01-a1b2c3r4etc.eu-central-1.es.amazonaws.com/index-name'
```
The following example shows how to delete all existing indices for a domain:
```sh
curl -XDELETE 'https://search-es-flowlogs-01-a1b2c3r4etc.eu-central-1.es.amazonaws.com/_all'
```

##### References
[1] - [AWS Docs - Working with Amazon Elasticsearch Service Index Snapshots](https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/es-managedomains-snapshots.html#es-managedomains-snapshot-registerdirectory)

[2] - [AWS Blogs - Use Amazon S3 to Store a Single Amazon Elasticsearch Service Index](https://aws.amazon.com/blogs/database/use-amazon-s3-to-store-a-single-amazon-elasticsearch-service-index/)
