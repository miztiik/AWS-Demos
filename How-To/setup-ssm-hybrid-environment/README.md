# AWS EC2 Systems Manager for Hybrid Cloud Management

AWS Systems Manager is a new way to manage your cloud and hybrid IT environments. It provides a unified user interface that simplifies resource and application management, shortens the time to detect and resolve operational problems, and makes it easy to operate and manage your infrastructure securely at scale.

![AWS EC2 SSM for Hybrid Cloud Management](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-ssm-hybrid-environment/images/AWS-EC2-Systems-Manager.png)

Follow this article in youtube: [Watch AWS EC2 SSM for Hybrid Cloud Management in Youtube](https://youtu.be/7GnxWvv8Z_M)

## AWS SSM Managed Instances Activations
A managed instance is any Amazon EC2 instance or on-premises machine in your hybrid environment that has been configured for Systems Manager. `Create Activation` for the required number of instances and note down the activation code and ID.
1. Click **Create Activation** : Update Activation Description
1. Choose **Instance Limit**
1. For **IAM Role Name**: Choose _Create a system default command execution role that has the required permissions_
   1. If you select this option, AWS creates a new role for you named `AmazonEC2RunCommandRoleForManagedInstances`
1. _Optional_: 
   1. Updated expiry date for activation
   1. `Default Instance Name`: _Assign a name that will help you to track the Managed Instances in the Console_
1. Click, **Create Activation**

```sh
You have successfully created a new activation (4ae70cf6-65fd-46fa-9547-b85dbe4d10a1).
Your activation code is listed below. Copy this code and keep it in a safe place as you will not be able to access it again.

        Activation Code: regAPcZL4voSsK2z5bTI
        Activation ID: 4ae70cf6-65fd-46fa-9547-b85dbe4d10a1

```

## Install SSM Client on On-Prem Server(s)
```sh
mkdir -p /tmp/ssm
curl https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm -o /tmp/ssm/amazon-ssm-agent.rpm
sudo yum install -y /tmp/ssm/amazon-ssm-agent.rpm
sudo systemctl stop amazon-ssm-agent
sudo amazon-ssm-agent -register -code "YOUR-ACTIVATION-CODE-HERE" -id "YOUR-ACTIVATION-ID-HERE" -region "ap-south-1"
sudo systemctl start amazon-ssm-agent
```

_**Note:** In the Amazon EC2 console, however, your on-premises instances are distinguished from Amazon EC2 instances with the prefix "**mi-**"._

## Validation: EC2 Run Command – Hybrid and Cross-Cloud Management
Now that your instances are managed by AWS, you can run commands on them. For example:
```
uptime
more /tmp/aws-ssm-hybrid-demo
```

### Troubleshooting
The SSM Agent logs information in the following files. The information in these files can help you troubleshoot problems,
```sh
/var/log/amazon/ssm/amazon-ssm-agent.log
/var/log/amazon/ssm/errors.log
```

##### Describe Registration
```sh
aws ssm describe-instance-information --instance-information-filter-list key=InstanceIds,valueSet=mi-00722d1fcb2c55ef8
```
