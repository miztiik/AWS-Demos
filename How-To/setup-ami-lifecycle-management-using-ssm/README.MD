# AMI LifeCycle Management Using EC2 Systems Manager | Automation

We will need two roles to automate the AMI LifeCycle Management.
1. **ManagedInstanceRole** - Role to allow SSM to start instances, create images etc,
   1. Add this managed policy `AmazonEC2RoleforSSM`
1. **AutomationServiceRole** - To Allow SSM to run documents and allow it to assume `ManagedInstanceRole`
   1. Add this managed policy `AmazonSSMAutomationRole`
   1. Inline Policy to attach the `iam:PassRole`
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

**Note:** - By default SSM Automation runs either the `AWS-UpdateLinuxAmi` document or the `AWS-UpdateWindowsAmi` in the default VPC. If you want it to run in a different VPC, then you should provide the subnets in the document, as shown in the [Example here](https://docs.aws.amazon.com/systems-manager/latest/userguide/automation-troubleshooting.html)




