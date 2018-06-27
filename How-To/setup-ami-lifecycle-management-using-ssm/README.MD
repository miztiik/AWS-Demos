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
1. **Trust Relationships**: Make the below trust relationship to both the roles

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
If this role creation and attaching trust policies, that part alone can be done using this [cloudformation template](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=Systems-Manager-AMI-Automation-Setup&templateURL=https://s3.amazonaws.com/aws-ssm-downloads-us-east-1/templates/automationsetup.yaml).


### Create Parameter for Golden AMI
Use the AWS CLI or GUI to create a parameter store entry, here is the CLI command. `BastionHost-Linux-AMI` is the parameter name that we will use in our _Automation_ Document and lambda will use the same to update the AMI Upon completion of the AMI.
```sh
aws ssm put-parameter --name BastionHost-Linux-AMI --value "ami-9a91b371" --type String
```

### Create [Lambda](https://docs.aws.amazon.com/systems-manager/latest/userguide/automation-simpatch.html#automation-pet1) to update SSM Parameter Store
This function will helps us to automatically update the parameter store with the latest AMI when the _Automation Document_ successfully create a new image.



**Customizations:**
_Modify as required for your environment_

1. Lambda Function Name: Choose it as `Automation-UpdateSsmParam`. If you change here, update the _Automation Document_ also with the same name.
   - Runtime should be `Python 2.7`
1. Choose the `lambda-ssm-role` you created earlier.
1. The `code` for lambda function is provided in this file `Automation-UpdateSsmParam.py`


### Create custom Automation Document

1. [Create Document](https://eu-central-1.console.aws.amazon.com/systems-manager/documents/create-document?region=eu-central-1), Give a **Name**, like "`BastionHost-Linux-AMI-Builder`.
1. Add the contents of the `BastionHost-Linux-AMI-Builder.json` file in the field.![](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-ami-lifecycle-management-using-ssm/images/Create-Automation-Document-00.png)
1. After succesful creation of the document, you should be able view,modify versions,![](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-ami-lifecycle-management-using-ssm/images/Create-Automation-Document-01.png)
**_Note:_** By default SSM Automation runs in the default VPC, If you are going to run in a different VPC, you **must** provide the subnet id, which has internet access.

### Creation of AMI
1. In the EC2 console, choose **Systems Manager Services,** **Automations**.![](https://media.amazonwebservices.com/blog/2017/EC2Sys-Console-1.png)
1. Choose **Execution automation** and pick the one we just created. Easiest way is to search by "_Owned by Me"_.
1. Expand **Document Details** and choose **Latest version at runtime**.![](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-ami-lifecycle-management-using-ssm/images/AWS-UpdateLinux-Ami.png)
1. Choose the latest document version.
1. For **Input Parameters**
   1. **SourceAmiId**, enter the ID of the Linux AMI to update.![](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-ami-lifecycle-management-using-ssm/images/AWS-UpdateLinux-Input-Parameters.png)
   1. For **InstanceProfileName**, enter the name of the managed instance. i.e `ManagedInstanceRole`
   1. For **AutomationAssumeRole**, enter the [**ARN**](http://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html#identifiers-arns) of the service role you created for Automation.
1.  Choose **Execute Automation**.
1.  Monitor progress in the **Automation Steps** tab, and view step-level outputs.

**Note:** - By default SSM Automation runs either the `AWS-UpdateLinuxAmi` document or the `AWS-UpdateWindowsAmi` in the default VPC.


### Pre-Update Script
Any packages/libraries/scripts that needs to be copied to the server before the update process begins.

### Post-Update Script
Optional: I have written a crude `post-ami-build.sh` script to install httpd and update the _index.html_ to test everything is working fine. Store the file in S3 and ensure the user who run SSM has access to the s3 bucket.

