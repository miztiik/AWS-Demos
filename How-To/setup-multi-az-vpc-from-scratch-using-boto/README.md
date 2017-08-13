# Setup Multi-AZ VPC from scratch using Boto3
In this demo, we are going to setup an VPC, which spans across mutliple availability zones, with different subnets. We will also see how to split up an CIDR range in a logical way across the multiple subnets. We will be doing all of this using Boto3.

#### Assumptions,
I am going to assume the reader is familiar with up AWS VPCs and using boto3,
- AWS Account
- Boto3 - Python familiarity

After we are done, we should be having a VPC architecture as shown below,
![Fig 1 : Multi-AZ VPC Configuration Context](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/img/multi-az-vpc.png)

### Define boto defaults:
We are going to use Asia Pacific Region, Our VPC will have 512 IPs, spread over two AZs each having their own set of 256 IPs. We will use CIDR Block `10.240.0.0/23`
```py
import boto3
globalVars  = {}
globalVars['REGION_NAME']              = "ap-south-1"
globalVars['AZ1']                      = "ap-south-1a"
globalVars['AZ2']                      = "ap-south-1b"
globalVars['CIDRange']                 = "10.240.0.0/23"

globalVars['az1_pvtsubnet_CIDRange']   = "10.240.0.0/25"
globalVars['az1_pubsubnet_CIDRange']   = "10.240.0.128/26"
globalVars['az1_sparesubnet_CIDRange'] = "10.240.0.192/26"

globalVars['az2_pvtsubnet_CIDRange']   = "10.240.1.0/25"
globalVars['az2_pubsubnet_CIDRange']   = "10.240.1.128/26"
globalVars['az2_sparesubnet_CIDRange'] = "10.240.1.192/26"

globalVars['tagProject']               = "Project"
globalVars['tagProjectName']           = "miztiik-vpc-demo"
globalVars['EC2-RH-AMI-ID']            = "ami-cdbdd7a2"
globalVars['EC2-Amazon-AMI-ID']        = "ami-3c89f653"
globalVars['EC2-InstanceType']         = "t2.micro"
globalVars['EC2-KeyName']              = "valaxy-key"
globalVars['EC2-InstanceType']         = "t2.micro"
```

_ToDo: Create the subnet split as variables, and remaining can be automated_

## Create VPC, Subnet, and Internet Gateway
```py
ec2         = boto3.resource ( 'ec2', region_name = globalVars['REGION_NAME'] )
ec2Client   = boto3.client   ( 'ec2', region_name = globalVars['REGION_NAME'] )
vpc         = ec2.create_vpc ( CidrBlock = globalVars['CIDRange']  )
```

## Create Subnets
We will create three subnets in each AZ, 
 - Private Subnet
 - Public Subnet
 - Spare Subnet
Since VPCs CIDR cannot be modified after they are created, we need to allocated some spare IPs in our VPC to accomodate future growth.

### In Availability Zone 01
For AZ1, We will allocated the CIDR `10.240.0.0/24` , i,e 256 IPs
```py
az1_pvtsubnet   = vpc.create_subnet( CidrBlock = globalVars['az1_pvtsubnet_CIDRange'], AvailabilityZone = globalVars['AZ1'] )
az1_pubsubnet   = vpc.create_subnet( CidrBlock = globalVars['az1_pubsubnet_CIDRange'], AvailabilityZone = globalVars['AZ1'] )
az1_sparesubnet = vpc.create_subnet( CidrBlock = globalVars['az1_sparesubnet_CIDRange'], AvailabilityZone = globalVars['AZ1'] )
```

### In Availability Zone 02
For AZ2, We will allocated the CIDR `10.240.1.0/24` , i,e 256 IPs
```py
az2_pvtsubnet   = vpc.create_subnet( CidrBlock = globalVars['az2_pvtsubnet_CIDRange'], AvailabilityZone = globalVars['AZ2'] )
az2_pubsubnet   = vpc.create_subnet( CidrBlock = globalVars['az2_pubsubnet_CIDRange'], AvailabilityZone = globalVars['AZ2'] )
az2_sparesubnet = vpc.create_subnet( CidrBlock = globalVars['az2_sparesubnet_CIDRange'], AvailabilityZone = globalVars['AZ2'] )

```

## Enable DNS Hostnames in the VPC
Enabling DNS Hostnames in the VPC allows AWS to generate public DNS routable _AWS hostnames_ for our EC2 Instances,
```py
ec2Client.modify_vpc_attribute( VpcId = vpc.id , EnableDnsSupport = { 'Value': True } )
ec2Client.modify_vpc_attribute( VpcId = vpc.id , EnableDnsHostnames = { 'Value': True } )
```

## Create the Internet Gateway & Attach to the VPC
EC2 instances require an internet gateway with in the VPC to route traffic to the internet.
```py
intGateway  = ec2.create_internet_gateway()
intGateway.attach_to_vpc( VpcId = vpc.id )
```

## Create route table for Public & Private traffic
Although there is a default route table for the VPC, it is advisable to have your own routable to allow for specific rules within the subnet. We will need to associate the route table with subnets specifically.
```py
routeTable = ec2.create_route_table( VpcId = vpc.id )
routeTable.associate_with_subnet( SubnetId = az1_pubsubnet.id )
routeTable.associate_with_subnet( SubnetId = az1_pvtsubnet.id )
routeTable.associate_with_subnet( SubnetId = az2_pubsubnet.id )
routeTable.associate_with_subnet( SubnetId = az2_pvtsubnet.id )
```

## Create a route for internet traffic to flow out
Create route in our table to allow internet traffic to pass through to any destination through our internet gateway.
```py
intRoute = ec2Client.create_route( RouteTableId = routeTable.id , DestinationCidrBlock = '0.0.0.0/0' , GatewayId = intGateway.id )
```

## Tag the resources
It is always a good idea to tag the resources. It allows for easier resource identification, classification and helps in billing.
```py
tag = vpc.create_tags               ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-vpc'}] )
tag = az1_pvtsubnet.create_tags     ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-az1-private-subnet'}] )
tag = az1_pubsubnet.create_tags     ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-az1-public-subnet'}] )
tag = az1_sparesubnet.create_tags   ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-az1-spare-subnet'}] )
tag = az2_pvtsubnet.create_tags     ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-az2-private-subnet'}] )
tag = az2_pubsubnet.create_tags     ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-az2-public-subnet'}] )
tag = az2_sparesubnet.create_tags   ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-az2-spare-subnet'}] )
tag = intGateway.create_tags        ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-igw'}] )
tag = routeTable.create_tags        ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-rtb'}] )
```

## Let create the Public & Private Security Groups
We will need separate security groups for our private and public instances for granular control. Further more, you may allow your private  instances only reachable from your public instances to increase security(although this is not shown here)
```py
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
```
#### Tag the Security Groups
```py
pubSecGrp.create_tags(Tags=[{'Key': globalVars['tagName'] ,'Value':'public-security-group'}])
pvtSecGrp.create_tags(Tags=[{'Key': globalVars['tagName'] ,'Value':'private-security-group'}])
```

#### Add a rule that allows inbound SSH, HTTP, HTTPS traffic ( from any source )
By default, **ALL** Inbound traffic in the security group is blocked. We need to create rules in our security group to allow certain ports/traffic,

As this is a demo, We will configure three ports,
 - Port 22 - _For SSH & Remote Administration_
 - Port 80 - _For HTTP Traffic_
 - Port 443 - _For HTTPS Traffic_
```py
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
```

### Exercise
 - Create an EC2 Instances in any of the subnets and try to ping the internet
_Point to Ponder: For ping you **may** need ICMP Port:)_

## Python Funtion to Cleanup AWS Resources,
It is a prudent to cleanup after you have successfully completed the demo, Call this function `cleanAll` only if you are sure of what you are doing, as this function **assumes** you are running it in the same terminal as the previous commands.

```py
"""
Function to clean up all the resources
"""
def cleanAll(resourcesDict=None):

    intGateway.delete()

    # Delete Subnets
    az1_pvtsubnet.delete()
    az1_pubsubnet.delete()
    az1_sparesubnet.delete()
    az2_pvtsubnet.delete()
    az2_pubsubnet.delete()
    az2_sparesubnet.delete()

    vpc.delete()
```