#!/usr/bin/python

### Set AWS Resources
# The AWS Resources options are set globally in python dict. This allows the user to customize the script to their region(for example change the region_name & AMI ID to your needs etc.,)
import boto3

globalVars = {}
globalVars['REGION_NAME']           = "ap-south-1"
globalVars['AZ1']                   = "ap-south-1a"
globalVars['AZ2']                   = "ap-south-1b"
globalVars['CIDRange']              = "10.244.0.0/24"
globalVars['tagName']               = "miztiik-demo-05-flowlogs"
globalVars['EC2-AMI-ID']            = "ami-cdbdd7a2"
globalVars['EC2-InstanceType']      = "t2.micro"
globalVars['EC2-KeyName']           = "flowlogs-key"
globalVars['Log-GroupName']         = "miztiik-demo-05-flowlogs"
globalVars['IAM-RoleName']          = "miztiik-demo-05-flowlogs-role"


### Setup Networks
# The VPC, Subnet, Internet Gateway, Routing Table & Security Groups are created as [described here](https://github.com/miztiik/AWS-Demos/tree/master/How-To/setup-multi-az-vpc-from-scratch-using-boto)
# Creating a VPC, Subnet, and Gateway
ec2         = boto3.resource ( 'ec2', region_name = globalVars['REGION_NAME'] )
ec2Client   = boto3.client   ( 'ec2', region_name = globalVars['REGION_NAME'] )
logsClient  = boto3.client   ( 'logs',region_name = globalVars['REGION_NAME'] )
iamClient   = boto3.client   ( 'iam', region_name = globalVars['REGION_NAME'] )

vpc         = ec2.create_vpc ( CidrBlock = globalVars['CIDRange'] )
# AZ1 Subnets
az1_pvtsubnet   = vpc.create_subnet( CidrBlock = '10.244.0.0/25'   , AvailabilityZone = globalVars['AZ1'] )
az1_pubsubnet   = vpc.create_subnet( CidrBlock = '10.244.0.128/26' , AvailabilityZone = globalVars['AZ1'] )
az1_sparesubnet = vpc.create_subnet( CidrBlock = '10.244.0.192/26' , AvailabilityZone = globalVars['AZ1'] )


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
from time import sleep
customEC2Keys = ec2Client.describe_key_pairs()['KeyPairs']
sleep(10)
if not next( ( key for key in customEC2Keys if key["KeyName"] == globalVars['EC2-KeyName'] ),False):
    ec2_key_pair = ec2.create_key_pair( KeyName = globalVars['EC2-KeyName'] )
    print ("New Private Key created,Save the below key-material\n\n")
    print ( ec2_key_pair.key_material )

# Create VPC Flow Logs
## We need to create a `Cloudwatch` Logs group that will be used by our log monitor
logGroup = logsClient.create_log_group( logGroupName = globalVars['Log-GroupName'],
                                        tags = {'Key': globalVars['tagName'] , 'Value':'Flow-Logs'}
                                        )

### Create IAM Role
flowLogsTrustPolicy = """{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "",
      "Effect": "Allow",
      "Principal": {
        "Service": "vpc-flow-logs.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
} 
"""

flowLogsPermissions = """{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}"""


#### Create the role with trust policy
iamRole = iamClient.create_role( RoleName = globalVars['IAM-RoleName'] ,
                                 AssumeRolePolicyDocument = flowLogsTrustPolicy
                                )

#### Attach permissions to the role
flowLogsPermPolicy = iamClient.create_policy( PolicyName    = "flowLogsPermissions",
                                              PolicyDocument= flowLogsPermissions,
                                              Description   = 'Provides permissions to publish flow logs to the specified log group in CloudWatch Logs'
                                            )

response = iamClient.attach_role_policy( RoleName = globalVars['IAM-RoleName'] ,
                                         PolicyArn= flowLogsPermPolicy['Policy']['Arn']
                                        )

sleep(10)

#### Creating flow logs with the IAM role and permissions
nwFlowLogs = ec2Client.create_flow_logs( ResourceIds              = [ vpc.id, ],
                                         ResourceType             = 'VPC',
                                         TrafficType              = 'ALL',
                                         LogGroupName             = globalVars['Log-GroupName'],
                                         DeliverLogsPermissionArn = iamRole['Role']['Arn']
                                        )

# EC2 Instance for traffic generation

# Using the userdata field, we will download, install webserver to generate some traffic
userDataCode = """
#!/bin/bash
set -e -x

# Install HTTP Server to generate some traffic
yum -y install httpd
systemctl start httpd
systemctl enable httpd
echo "<h1>Welcome to flow logs demo from Miztiik</h1>" >> /var/www/html/index.html
ping -c5 twitter.com
ping -c5 localhost
"""


##### **DeviceIndex**:The network interface's position in the attachment order. For example, the first attached network interface has a DeviceIndex of 0 
instanceLst = ec2.create_instances(ImageId = globalVars['EC2-AMI-ID'],
                                   MinCount=1,
                                   MaxCount=1,
                                   KeyName=globalVars['EC2-KeyName'] ,
                                   UserData = userDataCode,
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
18:34:26 2 566667777886 eni-86d38dee 123.108.200.124  10.244.0.139    123     38270 17 1  76   1490121266 1490121326 ACCEPT OK
18:34:26 2 566667777886 eni-86d38dee 10.244.0.139     139.59.19.184   47521   123   17 1  76   1490121266 1490121326 ACCEPT OK
18:34:26 2 566667777886 eni-86d38dee 10.244.0.139     122.166.159.156 80      49740 6  3  120  1490121266 1490121326 ACCEPT OK
18:34:26 2 566667777886 eni-86d38dee 10.244.0.139     122.166.159.156 80      49722 6  3  120  1490121266 1490121326 ACCEPT OK
18:34:26 2 566667777886 eni-86d38dee 94.233.207.244   10.244.0.139    8131    23    6  1  40   1490121266 1490121326 REJECT OK
18:34:26 2 566667777886 eni-86d38dee 10.244.0.139     209.132.183.107 42319   443   6  12 1474 1490121266 1490121326 ACCEPT OK
18:34:26 2 566667777886 eni-86d38dee 139.59.45.40     10.244.0.139    123     50535 17 1  76   1490121266 1490121326 ACCEPT OK
18:34:26 2 566667777886 eni-86d38dee 10.244.0.139     139.59.19.184   37270   123   17 1  76   1490121266 1490121326 ACCEPT OK
18:34:26 2 566667777886 eni-86d38dee 10.244.0.139     209.132.183.107 42320   443   6  14 1584 1490121266 1490121326 ACCEPT OK
18:34:26 2 566667777886 eni-86d38dee 209.132.183.107  10.244.0.139    443     42319 6  12 4633 1490121266 1490121326 ACCEPT OK
18:34:26 2 566667777886 eni-86d38dee 10.244.0.139     123.108.200.124 53652   123   17 1  76   1490121266 1490121326 ACCEPT OK
18:34:26 2 566667777886 eni-86d38dee 139.59.19.184    10.244.0.139    123     34449 17 1  76   1490121266 1490121326 ACCEPT OK
18:34:26 2 566667777886 eni-86d38dee 10.244.0.139     139.59.32.74 3  5676    123   17 1  76   1490121266 1490121326 ACCEPT OK

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

    # Delete Log Group & Flow Logs
    response = logsClient.delete_log_group( logGroupName = globalVars['Log-GroupName'] )
    response = ec2Client.delete_flow_logs( FlowLogIds = [ nwFlowLogs.id ] )
    
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

    # Detach & Delete IAM Role
    response = iamClient.detach_role_policy( RoleName = globalVars['IAM-RoleName'],
                                             PolicyArn= flowLogsPermPolicy['Policy']['Arn']
                                            )
    response = iamClient.delete_policy( PolicyArn = flowLogsPermPolicy['Policy']['Arn'] )
    response = iamClient.delete_role( RoleName = globalVars['IAM-RoleName'] )