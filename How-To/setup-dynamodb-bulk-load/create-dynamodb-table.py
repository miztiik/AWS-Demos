from __future__ import print_function 
import boto3
import json
from time import sleep

# Set the global variables
globalVars  = {}
globalVars['Owner']                 = "Miztiik"
globalVars['Environment']           = "Development"
globalVars['REGION_NAME']           = "eu-central-1"
globalVars['leadEmail']             = "kumar.searches+0@gmail.com"
globalVars['tableName']             = "sample_leads"
globalVars['leadExp']               = "4"

dynamodb = boto3.resource('dynamodb', region_name = globalVars['REGION_NAME'])

def create_ddb_table(table_name):

    response = dynamodb.create_table(TableName = table_name,
                      KeySchema = [{'AttributeName': 'exp', 'KeyType': 'HASH'}, #Partition key
                                   {'AttributeName': 'emailid', 'KeyType': 'RANGE'}, #Sort key
                                  ],
                      AttributeDefinitions = [{'AttributeType': 'N', 'AttributeName': 'exp'},
                                              {'AttributeType': 'S', 'AttributeName': 'emailid'},
                                              {'AttributeType': 'S', 'AttributeName': 'lead_status'},
                                              #{'AttributeType': 'BOOL', 'AttributeName': 'info.is_email_sent'}
                                             ],
                      GlobalSecondaryIndexes=[
                                             {
                                                 'IndexName': 'campaign-status-index',
                                                 'KeySchema': [
                                                     {'AttributeName': 'exp', 'KeyType': 'HASH'}, #Partition key
                                                     { 'AttributeName': 'lead_status', 'KeyType':'RANGE' } #Sort key
                                                 ],
                                                 'Projection': { 'ProjectionType': 'KEYS_ONLY' },
                                                 'ProvisionedThroughput': {
                                                     'ReadCapacityUnits': 2,
                                                     'WriteCapacityUnits': 2
                                                 }
                                             },
                                            ],
                      ProvisionedThroughput = {
                          'ReadCapacityUnits': 3,
                          'WriteCapacityUnits': 3
                          }
                          )
    return response

def get_table_metadata(table_name):
    """
    Get some metadata about chosen table.
    """
    table = dynamodb.Table(table_name)

    return {
        'num_items': table.item_count,
        'primary_key_name': table.key_schema[0],
        'status': table.table_status,
        'bytes_size': table.table_size_bytes,
        'global_secondary_indices': table.global_secondary_indexes
    }

# table.meta.client.get_waiter('table_exists').wait(TableName='users')

if __name__ == '__main__':
    resp = create_ddb_table(globalVars['tableName'])
    print("Table status:", resp.table_status)
    sleep(5)
    resp = get_table_metadata(resp.table_name)
    print("-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+")
    print(json.dumps(resp, indent=4))
    print("-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+")

# References
## [1] [Choosing the Right DynamoDB Partition Key](https://aws.amazon.com/blogs/database/choosing-the-right-dynamodb-partition-key/)
## [2] [Global Secondary Indexes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html)
## [3] [Take Advantage of Sparse Indexes](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-indexes-general-sparse-indexes.html#bp-indexes-sparse-examples)
## [4] [Best Practices for Querying and Scanning Data](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-query-scan.html)
## [5] [Querying on Multiple Attributes in Amazon DynamoDB](https://aws.amazon.com/blogs/database/querying-on-multiple-attributes-in-amazon-dynamodb/)

