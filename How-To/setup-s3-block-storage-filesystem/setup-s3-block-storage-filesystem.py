#!/usr/bin/python

### Set AWS Resources
# The AWS Resources options are set globally in python dict. This allows the user to customize the script to their region(for example change the region_name & AMI ID to your needs etc.,)
import boto3

globalVars = {}
globalVars['REGION_NAME']           = "ap-south-1"
globalVars['AZ1']                   = "ap-south-1a"
globalVars['AZ2']                   = "ap-south-1b"
globalVars['CIDRange']              = "10.243.0.0/24"
globalVars['tagName']               = "miztiik-s3fs-demo-04"
globalVars['EC2-AMI-ID']            = "ami-cdbdd7a2"
globalVars['EC2-InstanceType']      = "t2.micro"
globalVars['EC2-KeyName']           = "s3fs-key"
globalVars['S3-BucketName']         = "miztiik-demo-s3fs-bucket"

### Setup Networks
# The VPC, Subnet, Internet Gateway, Routing Table & Security Groups are created as [described here](https://github.com/miztiik/AWS-Demos/tree/master/How-To/setup-multi-az-vpc-from-scratch-using-boto)
# Creating a VPC, Subnet, and Gateway
ec2         = boto3.resource ( 'ec2', region_name = globalVars['REGION_NAME'] )
ec2Client   = boto3.client   ( 'ec2', region_name = globalVars['REGION_NAME'] )
s3Client    = boto3.client   ( 's3',  region_name = globalVars['REGION_NAME'] )

vpc         = ec2.create_vpc ( CidrBlock = globalVars['CIDRange'] )
# AZ1 Subnets
az1_pvtsubnet   = vpc.create_subnet( CidrBlock = '10.243.0.0/25'   , AvailabilityZone = globalVars['AZ1'] )
az1_pubsubnet   = vpc.create_subnet( CidrBlock = '10.243.0.128/26' , AvailabilityZone = globalVars['AZ1'] )
az1_sparesubnet = vpc.create_subnet( CidrBlock = '10.243.0.192/26' , AvailabilityZone = globalVars['AZ1'] )


# Enable DNS Hostnames in the VPC
vpc.modify_attribute( EnableDnsSupport = { 'Value': True } )
vpc.modify_attribute( EnableDnsHostnames = { 'Value': True } )

# Create the Internet Gatway & Attach to the VPC
intGateway  = ec2.create_internet_gateway()
intGateway.attach_to_vpc( VpcId = vpc.id )

# Create another route table for Public & Private traffic
routeTable = ec2.create_route_table( VpcId = vpc.id )

rtbAssn=[]
rtbAssn.append(routeTable.associate_with_subnet( SubnetId = az1_pubsubnet.id ))
rtbAssn.append(routeTable.associate_with_subnet( SubnetId = az1_pvtsubnet.id ))

# Create a route for internet traffic to flow out
intRoute = ec2Client.create_route( RouteTableId = routeTable.id, 
                                    DestinationCidrBlock = '0.0.0.0/0',
                                    GatewayId = intGateway.id
                                 )

# Tag the resources
tag = vpc.create_tags               ( Tags=[{'Key': globalVars['tagName'] , 'Value':'vpc'}] )
tag = az1_pvtsubnet.create_tags     ( Tags=[{'Key': globalVars['tagName'] , 'Value':'az1-private-subnet'}] )
tag = az1_pubsubnet.create_tags     ( Tags=[{'Key': globalVars['tagName'] , 'Value':'az1-public-subnet'}] )
tag = az1_sparesubnet.create_tags   ( Tags=[{'Key': globalVars['tagName'] , 'Value':'az1-spare-subnet'}] )
tag = intGateway.create_tags        ( Tags=[{'Key': globalVars['tagName'] , 'Value':'igw'}] )
tag = routeTable.create_tags        ( Tags=[{'Key': globalVars['tagName'] , 'Value':'rtb'}] )

# Let create the Public & Private Security Groups
pubSecGrp = ec2.create_security_group( DryRun = False, 
                              GroupName='pubSecGrp',
                              Description='Public_Security_Group',
                              VpcId= vpc.id
                            )

pvtSecGrp = ec2.create_security_group( DryRun = False, 
                              GroupName='pvtSecGrp',
                              Description='Private_Security_Group',
                              VpcId= vpc.id
                            )
pubSecGrp.create_tags(Tags=[{'Key': globalVars['tagName'] ,'Value':'public-security-group'}])
pvtSecGrp.create_tags(Tags=[{'Key': globalVars['tagName'] ,'Value':'private-security-group'}])


# Add a rule that allows inbound SSH, HTTP, HTTPS traffic ( from any source )
ec2Client.authorize_security_group_ingress( GroupId  = pubSecGrp.id ,
                                        IpProtocol= 'tcp',
                                        FromPort=80,
                                        ToPort=80,
                                        CidrIp='0.0.0.0/0'
                                        )
ec2Client.authorize_security_group_ingress( GroupId  = pubSecGrp.id ,
                                        IpProtocol= 'tcp',
                                        FromPort=443,
                                        ToPort=443,
                                        CidrIp='0.0.0.0/0'
                                        )
ec2Client.authorize_security_group_ingress( GroupId  = pubSecGrp.id ,
                                        IpProtocol= 'tcp',
                                        FromPort=22,
                                        ToPort=22,
                                        CidrIp='0.0.0.0/0'
                                        )

# Lets create the key-pair that we will use
### Check if key is already present
customEC2Keys = ec2Client.describe_key_pairs()['KeyPairs']
if not next((key for key in customEC2Keys if key["KeyName"] == globalVars['EC2-KeyName'] ),False):
    ec2_key_pair = ec2.create_key_pair( KeyName = globalVars['EC2-KeyName'] )
    print ("New Private Key created,Save the below key-material\n\n")
    print ( ec2_key_pair.key_material )

### Create S3 Bucket

# **No Validations** are being done to check for pre-existing bucket s
    # The bucket does not exist or you have no access.
s3Bucket = s3Client.create_bucket( ACL='private', 
                                   Bucket = globalVars['S3-BucketName'], 
                                   CreateBucketConfiguration = { 'LocationConstraint': globalVars['REGION_NAME'] }
                                )






# Create the S3-FS host Instance

# Using the userdata field, we will download, install & configure our basic word press website.
# The user defined code to install Wordpress, WebServer & Configure them
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
echo "This is a test text input" >>/var/s3fs-demo-fs/test-file-during-demo.txt
"""


##### **DeviceIndex**:The network interface's position in the attachment order. For example, the first attached network interface has a DeviceIndex of 0 
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

#### Sample Output
[root@ip-10-243-0-147 ~]# df -h /var/s3fs-demo-fs
Filesystem      Size  Used Avail Use% Mounted on
s3fs            256T     0  256T   0% /var/s3fs-demo-fs

[root@ip-10-243-0-147 ~]# more /var/s3fs-demo-fs/test-file-during-demo.txt
This is a test text input

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
    for key in bucket.objects.all():
        key.delete()
    s3Client.delete_bucket( Bucket = globalVars['S3-BucketName'] )