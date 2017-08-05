from __future__ import print_function

import json, urllib2, boto3


def lambda_handler(event, context):
    
    new_ip_ranges = ["1.2.3.4"]
    # response = urllib2.urlopen('https://ip-ranges.amazonaws.com/ip-ranges.json')
    # json_data = json.loads(response.read())
    # new_ip_ranges = [ x['ip_prefix'] for x in json_data['prefixes'] if x['service'] == 'cloudfront' ]
    # print(new_ip_ranges)

    ec2 = boto3.resource('ec2')
    security_group = ec2.securitygroup('sg-3xxexx5x')
    current_ip_ranges = [ x['cidrip'] for x in security_group.ip_permissions[0]['ipranges'] ]
    print(current_ip_ranges)

    params_dict = {
        u'prefixlistids': [],
        u'fromport': 0,
        u'ipranges': [],
        u'toport': 65535,
        u'ipprotocol': 'tcp',
        u'useridgrouppairs': []
    }

    authorize_dict = params_dict.copy()
    for ip in new_ip_ranges:
        if ip not in current_ip_ranges:
            authorize_dict['ipranges'].append({u'cidrip': ip})

    revoke_dict = params_dict.copy()
    for ip in current_ip_ranges:
        if ip not in new_ip_ranges:
            revoke_dict['ipranges'].append({u'cidrip': ip})

    print("the following new ip addresses will be added:")
    print(authorize_dict['ipranges'])

    print("the following new ip addresses will be removed:")
    print(revoke_dict['ipranges'])

    security_group.authorize_ingress(ippermissions=[authorize_dict])
    security_group.revoke_ingress(ippermissions=[revoke_dict])

    return {'authorized': authorize_dict, 'revoked': revoke_dict}