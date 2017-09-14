#!/usr/bin/env python
# -*- coding: utf-8 -*-

import boto3

__author__ = 'Mystique'

globalVars  = {}
globalVars['REGION_NAME']              = "ap-south-1"

globalVars['Project']                  = { 'Key':'Name',        'Value':'ELB-Demo'}
globalVars['tags']                     = [{'Key':'Owner',       'Value':'Miztiik'},
                                          {'Key':'Environment', 'Value':'Test'},
                                          {'Key':'Department',  'Value':'Valaxy-Training'}]

# Creating a VPC, Subnet, and Gateway
ec2         = boto3.resource ( 'ec2', region_name = globalVars['REGION_NAME'] )
ec2Client   = boto3.client   ( 'ec2', region_name = globalVars['REGION_NAME'] )


# If your tag's key is 'foo' and its value is 'production', you should change your code to the following.
# The Name is in the 'tag:key' format, and the Values are the values are the ones you are looking for that correspond to that key.
vpcIds=ec2Client.describe_vpcs(Filters = [{'Name':'tag:Name','Values': [ globalVars['Project']['Value']+'-vpc' ]}])

vpc.delete()











import boto3
import argparse

def get_vpcid(project, client):
    response = client.describe_vpcs(
        Filters = [{
            'Name': 'tag:Name',
            'Values': [
                project
            ]
        }
    ]
    )
    if len(response['Vpcs']) == 1:
        return response['Vpcs'][0]['VpcId']
    else:
        raise ValueError('More than one VPC returned!')

def get_route_tables(vpcid, resource):
    vpc = resource.Vpc(vpcid)
    route_tables = list(vpc.route_tables.all())
    return map(lambda route: route.id, route_tables)


def add_peering_route(route_table_id, cidr, peeringid, resource):
    route_table = resource.RouteTable(route_table_id)
    response = route_table.create_route(DestinationCidrBlock=cidr,
                                        VpcPeeringConnectionId=peeringid)


    return response

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--site', help='Name of the Site VPC', required=True)
    argparser.add_argument('--cidr', help='CIDR to add route for', required=True)
    argparser.add_argument('--peeringid', help='Peering connection we are going to use', required=True)
    argparser.add_argument('--profile', help='AWS Profile to use', required=True)
    args = argparser.parse_args()
    cidr = args.cidr
    site = args.site
    peeringid = args.peeringid
    profile = args.profile

    if profile != None: boto3.setup_default_session(profile_name=profile)
    ec2resource = boto3.resource('ec2', region_name='eu-central-1')
    ec2Client = boto3.client('ec2', region_name='eu-central-1')


    vpcid = get_vpcid(site, client = ec2Client)
    print('Looking up route tables for %s' % vpcid)
    route_tables = get_route_tables(vpcid, ec2resource)
    print ('Retrieved %s tables, proceeding to add tables' % len(route_tables))
    for table_id in route_tables:
        print('Adding route for %s to %s' % (cidr, peeringid))
        try:
            response = add_peering_route(table_id, cidr, peeringid, ec2resource)
            if response:
                continue
            else:
                print('Error occurred adding route to %s' % table_id)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'RouteAlreadyExists':
                print('Route already exists on %s, continuing' % table_id)
                continue
            else:
                print('Unexpected error: %s' % e)



    print('Routes have been added!')

if __name__ == '__main__':
    main()