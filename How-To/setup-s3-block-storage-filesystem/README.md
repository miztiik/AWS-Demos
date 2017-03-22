
# Setup S3 as a filesystem

![Setup S3 as a filesystem in EC2](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-s3-block-storage-filesystem/img/EC2-S3FS.png)

### Setup Networks
The VPC, Subnet, Internet Gateway, Routing Table & Security Groups are created as [described here](https://github.com/miztiik/AWS-Demos/tree/master/How-To/setup-multi-az-vpc-from-scratch-using-boto).

Customize the below global variables as needed,

```py
globalVars['tagName']               = "miztiik-s3fs-demo-04"
globalVars['EC2-AMI-ID']            = "ami-cdbdd7a2"
globalVars['EC2-InstanceType']      = "t2.micro"
globalVars['EC2-KeyName']           = "s3fs-key"
globalVars['S3-BucketName']         = "miztiik-demo-s3fs-bucket"
```

### Create S3 Bucket
```py
s3Bucket = s3Client.create_bucket( ACL='private', 
                                   Bucket = globalVars['S3-BucketName'], 
                                   CreateBucketConfiguration = { 'LocationConstraint': globalVars['REGION_NAME'] }
                                )
```
###### _**No Validations** are being done to check for pre-existing buckets_. It is preferable to create a new bucket, as we will be deleting it at the end of the exercise

### Create the S3-FS host Instance

Using the `userdata` field, we will download, install & configure `FUSE`(Filesystem in Userspace) packages needed to mount S3 as a filesystem.  To learn more about FUSE refer to [wiki](https://en.wikipedia.org/wiki/Filesystem_in_Userspace).

```sh
userDataCode = """
#!/bin/bash
set -e -x

# Install FUSE Packages
# Ref - https://github.com/s3fs-fuse/s3fs-fuse
yum -y install automake fuse fuse-devel gcc-c++ git libcurl-devel libxml2-devel make openssl-devel
git clone https://github.com/s3fs-fuse/s3fs-fuse.git
cd s3fs-fuse
./autogen.sh
./configure
make
make install

# Enter the Identity(Access-Key)&Credentials(Secret-Key)
echo "<A.C.C.E.S.S-K.E.Y>:<A.C.T.U.A.L-S.E.C.R.E.T-K.E.Y>" > /root/.s3fs-passwd
chmod 600 /root/.s3fs-passwd

# Mount s3fs with an existing bucket
mkdir -p /var/s3fs-demo-fs
s3fs miztiik-demo-s3fs-bucket /var/s3fs-demo-fs -o passwd_file=/root/.s3fs-passwd

# Write test in S3 File-System
echo "This is a test text input" >>/var/s3fs-demo-fs/test-file-during-demo.txt
"""
```

_**To automount during boot**_: Update the `/etc/fstab` as shown below,
```sh
echo -n "<bucket>    <mount_point> fuse.s3fs    _netdev,use_cache=/tmp,use_rrs=1,allow_other             0 0" >> /etc/fstab
```
###### **DeviceIndex**:The network interface's position in the attachment order. For example, the first attached network interface has a DeviceIndex of 0
```py
instanceLst = ec2.create_instances(ImageId = globalVars['EC2-AMI-ID'],
                                   MinCount=1,
                                   MaxCount=1,
                                   KeyName=globalVars['EC2-KeyName'] ,
                                   InstanceType = globalVars['EC2-InstanceType'],
                                   NetworkInterfaces=[
                                                        {
                                                            'SubnetId': az1_pubsubnet.id,
                                                            'Groups': [ pubSecGrp.id ],
                                                            'DeviceIndex':0,
                                                            'DeleteOnTermination': True,
                                                            'AssociatePublicIpAddress': True,
                                                        }
                                                    ]
                                )

```

#### Sample Output
```py
[root@ip-10-243-0-147 ~]# df -h /var/s3fs-demo-fs
Filesystem      Size  Used Avail Use% Mounted on
s3fs            256T     0  256T   0% /var/s3fs-demo-fs

[root@ip-10-243-0-147 ~]# more /var/s3fs-demo-fs/test-file-during-demo.txt
This is a test text input
```

### AWS Resource CleanUp
```py
"""
Function to clean up all the resources
"""
def cleanAll(resourcesDict=None):

    # Delete the instances
    ids=[]
    for i in instanceLst:
        ids.append(i.id)

    ec2.instances.filter(InstanceIds=ids).terminate()
    
    # Wait for the instance to be terminated
    # Boto waiters might be best, for this demo, i will will "sleep"
    from time import sleep
    sleep(120)

    ec2Client.delete_key_pair( KeyName = globalVars['EC2-KeyName'] )
    
    # Delete Routes & Routing Table
    for assn in rtbAssn:
        ec2Client.disassociate_route_table( AssociationId = assn.id )

    routeTable.delete()

    # Delete Subnets
    az1_pvtsubnet.delete()
    az1_pubsubnet.delete()
    az1_sparesubnet.delete()

    # Detach & Delete internet Gateway
    ec2Client.detach_internet_gateway( InternetGatewayId = intGateway.id , VpcId = vpc.id )
    intGateway.delete()

    # Delete Security Groups
    pubSecGrp.delete()
    pvtSecGrp.delete()

    # Delete VPC
    vpc.delete()

    # Delete S3 Bucket
    s3 = boto3.resource( 's3',  region_name = globalVars['REGION_NAME'] )
    bucket = s3.Bucket( globalVars['S3-BucketName'] )
    for key in bucket.objects.all():
        key.delete()
    bucket.delete()
```