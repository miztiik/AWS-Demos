#!/usr/bin/python
# -*- coding: utf-8 -*-
import boto3, json, logging
from botocore.client import Config
from botocore.exceptions import ClientError
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
globalVars['DefaultExpiry']         = "10"

logger = logging.getLogger()


def signed_get_url(event):
    """Function to generate the presigned GET url, that can be used to retrieve objects from s3 bucket
    Required Bucket Name and Object Name to generate url
    """
    s3 = boto3.client('s3', region_name = 'eu-central-1',config=Config(signature_version='s3v4'))
    bodyData = json.loads(event['body'])
    try:
        url = s3.generate_presigned_url(ClientMethod='get_object',
                                        ExpiresIn=int(globalVars['DefaultExpiry']),
                                        Params={'Bucket': bodyData["BucketName"],
                                                'Key':bodyData["ObjectName"]
                                               } 
                                        )
        # Browser requires this header to allow cross domain requests
        head = {"Access-Control-Allow-Origin" : "*" }
        body = { 'PreSignedUrl':url }
        response = {'statusCode': 200, 'body': json.dumps(body), 'headers':head}
    except Exception as e:
        logger.error('Unable to generate URL')
        logger.error('ERROR: {0}'.format( str(e) ) )
        response = {'statusCode': 502, 'body': 'Unable to generate URL', 'headers':head}
        pass
    return response


def signed_post_url(event):
    """Function to generate the presigned post url, that can be used to upload objects to s3 bucket
    Required Bucket Name and Object Name to generate url
    """
    s3 = boto3.client('s3')
    import uuid
    bodyData = json.loads(event['body'])
    # Add random prefix - Although not necessary to improve s3 performance, to avoid overwrite of existing objects.
    fName = uuid.uuid4().hex + '_' + bodyData['FileName']
    try:
        post = s3.generate_presigned_post(Bucket=bodyData["BucketName"],Key=fName)
        # Browser requires this header to allow cross domain requests
        head = {"Access-Control-Allow-Origin" : "*" }
        response = {'statusCode': 200, 'body': json.dumps(post), 'headers':head}
    except Exception as e:
        logger.error('Unable to generate PUT Url')
        logger.error('ERROR: {0}'.format( str(e) ) )
        response = {'statusCode': 502, 'body': 'Unable to generate URL', 'headers':head}
        pass
    return response

def lambda_handler(event, context):
    if event['body']:
        # Lets convert the post body back into a dictionary
        bodyData = json.loads(event['body'])
        if bodyData['methodType'] == 'GET':
            response = signed_get_url(event)
        elif bodyData['methodType'] == 'POST':
            response = signed_post_url(event)
        else:
            body = {'Message':'Unable to generate URL, Re-Check your Bucket/Object Name'}
            head = {"Access-Control-Allow-Origin" : "*" }
            response = {'statusCode': 403, 'body': json.dumps(body), 'headers':head}
    return response

if __name__ == '__main__':
    lambda_handler(None, None)
