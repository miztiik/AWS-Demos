from __future__ import print_function # Python 2/3 compatibility
import boto3
import json
import time
import uuid
from time import sleep
from decimal import Decimal

# Set the global variables
globalVars  = {}
globalVars['Owner']                 = "Miztiik"
globalVars['Environment']           = "Development"
globalVars['REGION_NAME']           = "eu-central-1"
globalVars['leadEmail']             = "kumar.searches+0@gmail.com"
globalVars['tableName']             = "sample_leads"
globalVars['leadExp']               = "4"

dynamodb = boto3.resource('dynamodb', region_name='eu-central-1')

table = dynamodb.Table( globalVars['tableName'] )

leads_filename="sample-leads-02.json"
#leads_filename="campaign-leads.json"

def gen_uuid():
    return str( uuid.uuid4() )


def dict_to_item(raw):
    """
    Coverts a standard Python dictionary to a Boto3 DynamoDB item
    """
    if isinstance(raw, dict):
        return {
            'M': {
                k: dict_to_item(v)
                for k, v in raw.items()
            }
        }
    elif isinstance(raw, list):
        return {
            'L': [dict_to_item(v) for v in raw]
        }
    elif isinstance(raw, str):
        return {'S': raw}
    elif isinstance(raw, int):
        return {'N': str(raw)}

with open(leads_filename) as json_file:
    leads = json.load(json_file, parse_float = Decimal)
    # For fetching unique items from DDB
    future_time = 66659500800
    leadid = future_time
    for num, lead in enumerate(leads, start =1):
        info = {}
        # The experience of people is rounded off to an integer, 
        # If no experience is found they are given 1 yr of experience. As this key is the primary key for GSI
        # Would like to be able to query for gt > 0 to find some values if there are no leads in other paritions
        if 'exp' in lead:
            exp = int(round(Decimal(lead['exp'])))
        else:
            exp = int(1)
        # leadid = int(time.time())
        leadid += num

        # Lets set all status to "PENDING"
        lead_status = "PENDING" + "-" + lead['emailid']

        table.put_item(
           Item = {
               'emailid'        : lead['emailid'],
               'exp'            : exp,
               'lead_status'    : lead_status,
               'name'           : lead['name'],
               'keyskills'      : lead['keyskills'],
               'mobile'         : lead['mobile'],
            }
        )
        print("Added lead:"+lead['emailid'], exp, lead_status)
        sleep(2)
