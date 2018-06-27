# AMI LifeCycle Management Using EC2 Systems Manager | Automation

We will need two roles to automate the AMI LifeCycle Management.
1. RoleName: **lambda-ssm-role**: 
   - Permissions: Managed Policies `AWSLambdaExecute` and `AmazonSSMFullAccess`
1. RoleName: **ManagedInstanceRole**: - An EC2 Role to allow SSM to start instances, create images etc,
   - Permissions: Managed Policies `AmazonEC2RoleforSSM`
1. RoleName: **AutomationServiceRole**: - An EC2 Role to Allow SSM to run documents and allow it to assume _ManagedInstanceRole_ we just created.
   - Permissions: Managed Policies `AmazonSSMAutomationRole`
   - Inline Policy to attach the `iam:PassRole`
    ```
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "VisualEditor0",
                "Effect": "Allow",
                "Action": "iam:PassRole",
                "Resource": "arn:aws:iam::<YOUR-ACCOUNT-NUMBER>:role/<your-ManagedInstanceRole-name"
            }
        ]
    }
    ```

## Trust Relationships
Make the below trust relationship to both the roles

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "ec2.amazonaws.com",
          "ssm.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```
If this is all too much for you, you can use this [cloudformation template to create the same](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=Systems-Manager-AMI-Automation-Setup&templateURL=https://s3.amazonaws.com/aws-ssm-downloads-us-east-1/templates/automationsetup.yaml)


### Create [Lambda](https://docs.aws.amazon.com/systems-manager/latest/userguide/automation-simpatch.html#automation-pet1) to update SSM Parameter Store

**Customizations:**
_Modify as required for your environment_
1. SSM Parameter Name for `Golden AMI` - Default is `BastionHost-Linux-AMI` 
1. Lambda Function Name: Default is `Automation-UpdateSsmParam`


```py
from __future__ import print_function

import json
import boto3

print('Loading function')


#Updates an SSM parameter
#Expects parameterName, parameterValue
def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    # get SSM client
    client = boto3.client('ssm')

    #confirm  parameter exists before updating it
    response = client.describe_parameters(
       Filters=[
          {
           'Key': 'Name',
           'Values': [ event['parameterName'] ]
          },
        ]
    )

    if not response['Parameters']:
        print('No such parameter')
        return 'SSM parameter not found.'

    #if parameter has a Descrition field, update it PLUS the Value
    if 'Description' in response['Parameters'][0]:
        description = response['Parameters'][0]['Description']
        
        response = client.put_parameter(
          Name=event['parameterName'],
          Value=event['parameterValue'],
          Description=description,
          Type='String',
          Overwrite=True
        )
    
    #otherwise just update Value
    else:
        response = client.put_parameter(
          Name=event['parameterName'],
          Value=event['parameterValue'],
          Type='String',
          Overwrite=True
        )
        
    reponseString = 'Updated parameter %s with value %s.' % (event['parameterName'], event['parameterValue'])
        
    return reponseString
    ```



### Creation of AMI
1. In the EC2 console, choose **Systems Manager Services,** **Automations**.![](https://media.amazonwebservices.com/blog/2017/EC2Sys-Console-1.png)
1. Choose **Execution automation** and scroll down to update details.
1. Expand **Document Details** and choose **Latest version at runtime**.![](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-ami-lifecycle-management-using-ssm/images/AWS-UpdateLinux-Ami.png)
1. Choose the latest document version.
1. For **Input Parameters**
   1. **SourceAmiId**, enter the ID of the Linux AMI to update.![](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-ami-lifecycle-management-using-ssm/images/AWS-UpdateLinux-Input-Parameters.png)
   1. For **InstanceProfileName**, enter the name of the managed instance. i.e `ManagedInstanceRole`
   1. For **AutomationAssumeRole**, enter the [**ARN**](http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html#identifiers-arns) of the service role you created for Automation.
1.  Choose **Execute Automation**.
1.  Monitor progress in the **Automation Steps** tab, and view step-level outputs.

**Note:** - By default SSM Automation runs either the `AWS-UpdateLinuxAmi` document or the `AWS-UpdateWindowsAmi` in the default VPC. If you want it to run in a different VPC, then you should provide the subnets in the document, as shown in the [example here](https://docs.aws.amazon.com/systems-manager/latest/userguide/automation-troubleshooting.html)


### Pre-Update Script
Any packages/libraries/scripts that needs to be copied to the server before the update process begins.

### Post-Update Script
1. **AMI Validation Scripts:** If you have any testing to be done on the newly created AMI, this is the place, where you will have to do it. 
1. **Update Parameter Store:** After successful completion of test, update the AMI value into the parameter store using Lambda functions


