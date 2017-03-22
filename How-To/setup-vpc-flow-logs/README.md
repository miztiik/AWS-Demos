VPC Flow Logs – Log and View Network Traffic Flows
Many organizations collect, store, and analyze network flow logs. They use this information to troubleshoot connectivity and security issues, and to make sure that network access rules are working as expected.

VPC Flow Logs is a feature that enables you to capture information about the IP traffic going to and from network interfaces in your VPC. Flow log data is stored using Amazon CloudWatch Logs. After you've created a flow log, you can view and retrieve its data in Amazon CloudWatch Logs.



### Things you need
 - VPC
 -- Enable VPC Flow Logs
 - Log Groups
 - IAM Role

### Global Variables
Lets set these global variables that will be used throughout this demo,
```py
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
```

### Setup Networks

#### Creating a VPC, Subnet, and Internet Gateway
The VPC, Subnet, Internet Gateway, Routing Table & Security Groups are created as [described here](https://github.com/miztiik/AWS-Demos/tree/master/How-To/setup-multi-az-vpc-from-scratch-using-boto)

#### Boto3 Clients for Logs & IAM
We will also need to create clients for CloudWatch Logs & IAM
```py
logsClient  = boto3.client   ( 'logs',region_name = globalVars['REGION_NAME'] )
iamClient   = boto3.client   ( 'iam', region_name = globalVars['REGION_NAME'] )
```

# Create VPC Flow Logs
 _The IAM role that's associated with your flow log must have sufficient permissions to publish flow logs to the specified log group in CloudWatch Logs._

 _We must also ensure that our role has a **trust relationship** that allows the flow logs service to assume the role_

 _Trust policies specifies which trusted accounts are allowed to grant its users permissions to assume the role. Trust policies do not contain a resource element as these policies are attached to the resource (in this case a role)._


### Create a `Cloudwatch` Logs group 
```
logGroup = logsClient.create_log_group( logGroupName = globalVars['Log-GroupName'],
                                        tags = {'Key': globalVars['tagName'] , 'Value':'Flow-Logs'}
                                        )
```

### Create IAM Role
```py
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
```

#### Create the role with trust policy
```py
iamRole = iamClient.create_role( RoleName = globalVars['IAM-RoleName'] ,
                                 AssumeRolePolicyDocument = flowLogsTrustPolicy
                                )
```

#### Attach permissions to the role
```py
flowLogsPermPolicy = iamClient.create_policy( PolicyName    = "flowLogsPermissions",
                                              PolicyDocument= flowLogsPermissions,
                                              Description   = 'Provides permissions to publish flow logs to the specified log group in CloudWatch Logs'
                                            )

response = iamClient.attach_role_policy( RoleName = globalVars['IAM-RoleName'] ,
                                         PolicyArn= flowLogsPermPolicy['Policy']['Arn']
                                        )
```

#### Creating flow logs with the IAM role and permissions

```py
nwFlowLogs = ec2Client.create_flow_logs( ResourceIds              = [ vpc.id, ],
                                         ResourceType             = 'VPC',
                                         TrafficType              = 'ALL',
                                         LogGroupName             = globalVars['Log-GroupName'],
                                         DeliverLogsPermissionArn = iamRole['Role']['Arn']
                                        )
```

# EC2 Instance for traffic generation
```sh
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
```
#### Sample Output
 _Flows are collected, processed, and stored in capture windows that are approximately 10 minutes long. The log group will be created and the first flow records will become visible in the console about ten minutes after you create the Flow Log._
```
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
```

### Cleanup AWS Resources
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
```

  
