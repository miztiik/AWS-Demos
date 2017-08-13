#!/usr/bin/python
# -*- coding: utf-8 -*-

# VPC design for multi az deployments

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
globalVars['tagProjectName']           = "miztiik-elb-demo"
globalVars['EC2-RH-AMI-ID']            = "ami-cdbdd7a2"
globalVars['EC2-Amazon-AMI-ID']        = "ami-3c89f653"
globalVars['EC2-InstanceType']         = "t2.micro"
globalVars['EC2-KeyName']              = "valaxy-key"
globalVars['EC2-InstanceType']         = "t2.micro"


# Creating a VPC, Subnet, and Gateway
ec2         = boto3.resource ( 'ec2', region_name = globalVars['REGION_NAME'] )
ec2Client   = boto3.client   ( 'ec2', region_name = globalVars['REGION_NAME'] )
vpc         = ec2.create_vpc ( CidrBlock = globalVars['CIDRange']  )


# AZ1 Subnets
az1_pvtsubnet   = vpc.create_subnet( CidrBlock = globalVars['az1_pvtsubnet_CIDRange'], AvailabilityZone = globalVars['AZ1'] )
az1_pubsubnet   = vpc.create_subnet( CidrBlock = globalVars['az1_pubsubnet_CIDRange'], AvailabilityZone = globalVars['AZ1'] )
az1_sparesubnet = vpc.create_subnet( CidrBlock = globalVars['az1_sparesubnet_CIDRange'], AvailabilityZone = globalVars['AZ1'] )
# AZ2 Subnet
az2_pvtsubnet   = vpc.create_subnet( CidrBlock = globalVars['az2_pvtsubnet_CIDRange'], AvailabilityZone = globalVars['AZ2'] )
az2_pubsubnet   = vpc.create_subnet( CidrBlock = globalVars['az2_pubsubnet_CIDRange'], AvailabilityZone = globalVars['AZ2'] )
az2_sparesubnet = vpc.create_subnet( CidrBlock = globalVars['az2_sparesubnet_CIDRange'], AvailabilityZone = globalVars['AZ2'] )

# Enable DNS Hostnames in the VPC
vpc.modify_attribute( EnableDnsSupport = { 'Value': True } )
vpc.modify_attribute( EnableDnsHostnames = { 'Value': True } )

# Create the Internet Gatway & Attach to the VPC
intGateway  = ec2.create_internet_gateway()
intGateway.attach_to_vpc( VpcId = vpc.id )

# Create another route table for Public & Private traffic
routeTable = ec2.create_route_table( VpcId = vpc.id )
routeTable.associate_with_subnet( SubnetId = az1_pubsubnet.id )
routeTable.associate_with_subnet( SubnetId = az1_pvtsubnet.id )
routeTable.associate_with_subnet( SubnetId = az2_pubsubnet.id )
routeTable.associate_with_subnet( SubnetId = az2_pvtsubnet.id )

# Create a route for internet traffic to flow out
intRoute = ec2Client.create_route( RouteTableId = routeTable.id , DestinationCidrBlock = '0.0.0.0/0' , GatewayId = intGateway.id )

# Tag the resources
tag = vpc.create_tags               ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-vpc'}] )
tag = az1_pvtsubnet.create_tags     ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-az1-private-subnet'}] )
tag = az1_pubsubnet.create_tags     ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-az1-public-subnet'}] )
tag = az1_sparesubnet.create_tags   ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-az1-spare-subnet'}] )
tag = az2_pvtsubnet.create_tags     ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-az2-private-subnet'}] )
tag = az2_pubsubnet.create_tags     ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-az2-public-subnet'}] )
tag = az2_sparesubnet.create_tags   ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-az2-spare-subnet'}] )
tag = intGateway.create_tags        ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-igw'}] )
tag = routeTable.create_tags        ( Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key':'Name', 'Value':globalVars['tagProjectName']+'-rtb'}] )

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

pubSecGrp.create_tags(Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key': 'Name' ,'Value': globalVars['tagProjectName']+'-public-security-group'}])
pvtSecGrp.create_tags(Tags=[{'Key':globalVars['tagProject'], 'Value':globalVars['tagProjectName']}, {'Key': 'Name' ,'Value': globalVars['tagProjectName']+'-private-security-group'}])

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