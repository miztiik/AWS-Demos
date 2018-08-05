#!/usr/bin/python
# -*- coding: utf-8 -*-
import boto3, json, logging
from botocore.client import Config
from botocore.exceptions import ClientError
from botocore.vendored import requests
# Set the global variables
"""
Can Override the global variables using Lambda Environment Parameters
"""
globalVars  = {}
globalVars['Owner']                 = "Mystique"
globalVars['Environment']           = "Test"
globalVars['REGION_NAME']           = "eu-central-1"
globalVars['tagName']               = "Pre-Signed-Url-Generator"
globalVars['BucketName']            = "secure-pvt-bucket"
globalVars['SNSTopicArn']           = ""
logger = logging.getLogger()
def signed_get_url(event):

    s3 = boto3.client('s3', region_name = 'eu-central-1',config=Config(signature_version='s3v4'))
    bodyData = json.loads(event['body'])
    try:
        url = s3.generate_presigned_url(ClientMethod='get_object', ExpiresIn=10, Params={'Bucket': bodyData["BucketName"], 'Key':bodyData["ObjectName"] } )
        head = {"Access-Control-Allow-Origin" : "*" }
        body = { 'PreSignedUrl':url }
        response = {'statusCode': 200, 'body': json.dumps(body), 'headers':head}
    except Exception as e:
        logger.error('Unable to generate URL')
        logger.error('ERROR: Unable to generate URL. {0}'.format( str(e) ) )
        response = {'statusCode': 502, 'body': 'Unable to generate URL', 'headers':head}
        pass
    return response

def signed_post_url(event):
    s3 = boto3.client('s3')
    import uuid

    
    bodyData = json.loads(event['body'])
    fName = uuid.uuid4().hex + '_' + bodyData['FileName']
    #fName = bodyData['FileName']
    post = s3.generate_presigned_post(Bucket=bodyData["BucketName"],Key=fName)
    
    head = {"Access-Control-Allow-Origin" : "*" }
    body = { 'FileName':'called POST method, Everything good up here' }
    response = {'statusCode': 200, 'body': json.dumps(post), 'headers':head}
    return response

def lambda_handler(event, context):
    # Check if the POST has body message
    logger.error(json.dumps(event))
    if event['body']:
        # Lets convert the post body back into a dictionary
        bodyData = json.loads(event['body'])
        if bodyData['methodType'] == 'GET':
            get_url = signed_get_url(event)
        elif bodyData['methodType'] == 'POST':
            get_url = signed_post_url(event)
        else:
            body = {'Message':'Unable to generate URL, Re-Check your Bucket/Object Name'}
            head = {"Access-Control-Allow-Origin" : "*" }
            response = {'statusCode': 403, 'body': json.dumps(body), 'headers':head}
    return get_url

if __name__ == '__main__':
    lambda_handler(None, None)
