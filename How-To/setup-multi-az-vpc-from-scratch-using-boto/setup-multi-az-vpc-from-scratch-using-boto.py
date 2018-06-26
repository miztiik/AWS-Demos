#!/usr/bin/python
# -*- coding: utf-8 -*-

# VPC design for Multi AZ deployments & Tag all resources.

import boto3

globalVars  = {}
globalVars['REGION_NAME']              = "us-east-1"
globalVars['AZ1']                      = "us-east-1a"
globalVars['AZ2']                      = "us-east-1b"
globalVars['CIDRange']                 = "10.82.0.0/23"

globalVars['az1_pvtsubnet_CIDRange']   = "10.82.0.0/25"
globalVars['az1_pubsubnet_CIDRange']   = "10.82.0.128/26"
globalVars['az1_sparesubnet_CIDRange'] = "10.82.0.192/26"

globalVars['az2_pvtsubnet_CIDRange']   = "10.82.1.0/25"
globalVars['az2_pubsubnet_CIDRange']   = "10.82.1.128/26"
globalVars['az2_sparesubnet_CIDRange'] = "10.82.1.192/26"
globalVars['Project']                  = { 'Key':'Name',        'Value':'Test-01'}
globalVars['tags']                     = [{'Key':'Owner',       'Value':'Miztiik'},
                                          {'Key':'Environment', 'Value':'Test'},
                                          {'Key':'Department',  'Value':'Training'},
                                          {'Key':'CostCenter',  'Value':'NL-Labs'}]
globalVars['EC2-KeyName']              = globalVars['Project']['Value']+'-Key'

# Creating a VPC, Subnet, and Gateway
ec2         = boto3.resource ( 'ec2', region_name = globalVars['REGION_NAME'] )
ec2Client   = boto3.client   ( 'ec2', region_name = globalVars['REGION_NAME'] )
vpc         = ec2.create_vpc ( CidrBlock = globalVars['CIDRange'] )


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

# Create another route table for Public traffic
pubRouteTable = ec2.create_route_table( VpcId = vpc.id )
pubRouteTable.associate_with_subnet( SubnetId = az1_pubsubnet.id )
pubRouteTable.associate_with_subnet( SubnetId = az2_pubsubnet.id )

# Create another route table for Private traffic
pvtRouteTable = ec2.create_route_table( VpcId = vpc.id )
pvtRouteTable.associate_with_subnet( SubnetId = az1_pvtsubnet.id )
pvtRouteTable.associate_with_subnet( SubnetId = az2_pvtsubnet.id )

# Create a route for internet traffic to flow out
intRoute = ec2Client.create_route( RouteTableId = pubRouteTable.id , DestinationCidrBlock = '0.0.0.0/0' , GatewayId = intGateway.id )

# Tag the resources
vpc.create_tags               ( Tags = globalVars['tags'] )
az1_pvtsubnet.create_tags     ( Tags = globalVars['tags'] )
az1_pubsubnet.create_tags     ( Tags = globalVars['tags'] )
az1_sparesubnet.create_tags   ( Tags = globalVars['tags'] )
az2_pvtsubnet.create_tags     ( Tags = globalVars['tags'] )
az2_pubsubnet.create_tags     ( Tags = globalVars['tags'] )
az2_sparesubnet.create_tags   ( Tags = globalVars['tags'] )
intGateway.create_tags        ( Tags = globalVars['tags'] )
pubRouteTable.create_tags     ( Tags = globalVars['tags'] )
pvtRouteTable.create_tags     ( Tags = globalVars['tags'] )

vpc.create_tags               ( Tags = [{'Key':'Name', 'Value':globalVars['Project']['Value']+'-vpc'}] )
az1_pvtsubnet.create_tags     ( Tags = [{'Key':'Name', 'Value':globalVars['Project']['Value']+'-az1-private-subnet'}] )
az1_pubsubnet.create_tags     ( Tags = [{'Key':'Name', 'Value':globalVars['Project']['Value']+'-az1-public-subnet'}] )
az1_sparesubnet.create_tags   ( Tags = [{'Key':'Name', 'Value':globalVars['Project']['Value']+'-az1-spare-subnet'}] )
az2_pvtsubnet.create_tags     ( Tags = [{'Key':'Name', 'Value':globalVars['Project']['Value']+'-az2-private-subnet'}] )
az2_pubsubnet.create_tags     ( Tags = [{'Key':'Name', 'Value':globalVars['Project']['Value']+'-az2-public-subnet'}] )
az2_sparesubnet.create_tags   ( Tags = [{'Key':'Name', 'Value':globalVars['Project']['Value']+'-az2-spare-subnet'}] )
intGateway.create_tags        ( Tags = [{'Key':'Name', 'Value':globalVars['Project']['Value']+'-igw'}] )
pubRouteTable.create_tags     ( Tags = [{'Key':'Name', 'Value':globalVars['Project']['Value']+'-rtb'}] )
pvtRouteTable.create_tags     ( Tags = [{'Key':'Name', 'Value':globalVars['Project']['Value']+'-rtb'}] )
# Let create the Public & Private Security Groups
elbSecGrp = ec2.create_security_group( DryRun = False,
                              GroupName='elbSecGrp',
                              Description='ElasticLoadBalancer_Security_Group',
                              VpcId= vpc.id
                            )

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


elbSecGrp.create_tags( Tags = globalVars['tags'] )
pubSecGrp.create_tags( Tags = globalVars['tags'] )
pvtSecGrp.create_tags( Tags = globalVars['tags'] )

elbSecGrp.create_tags(Tags=[{'Key': 'Name' ,'Value': globalVars['Project']['Value']+'-elb-security-group'}])
pubSecGrp.create_tags(Tags=[{'Key': 'Name' ,'Value': globalVars['Project']['Value']+'-public-security-group'}])
pvtSecGrp.create_tags(Tags=[{'Key': 'Name' ,'Value': globalVars['Project']['Value']+'-private-security-group'}])

# Add a rule that allows inbound SSH, HTTP, HTTPS traffic ( from any source )
ec2Client.authorize_security_group_ingress( GroupId  = elbSecGrp.id ,
                                        IpProtocol= 'tcp',
                                        FromPort=80,
                                        ToPort=80,
                                        CidrIp='0.0.0.0/0'
                                        )

# Allow Public Security Group to receive traffic from ELB Security group
ec2Client.authorize_security_group_ingress( GroupId = pubSecGrp.id,
                                            IpPermissions = [{'IpProtocol': 'tcp',
                                                               'FromPort': 80,
                                                               'ToPort': 80,
                                                               'UserIdGroupPairs': [{ 'GroupId':elbSecGrp.id}]
                                                             }]
                                           )
# Allow Private Security Group to receive traffic from Application Security group
ec2Client.authorize_security_group_ingress( GroupId = pvtSecGrp.id,
                                            IpPermissions = [{'IpProtocol': 'tcp',
                                                               'FromPort': 80,
                                                               'ToPort': 80,
                                                               'UserIdGroupPairs': [{ 'GroupId':pubSecGrp.id}]
                                                             }]
                                           )

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