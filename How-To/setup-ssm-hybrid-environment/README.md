# Amazon EC2 Systems Manager for Hybrid Cloud Management

## Pre-Requisites
1. IAM Role for SSM - `AmazonSSMFullAccess`; _(You can also configure with more restrictive policies)_
1. _Atleast_ one Linux/Windows "On-Prem" Instance - _This demo uses a RHEL7 Instances_
   1. _Preferably this instance should not in AWS Cloud_ 
   1. _For AWS Instances you can run them with with IAM Role to connect with AWS SSM_

![AWS EC2 SSM for Hybrid Cloud Management](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-ssm-hybrid-environment/images/AWS-SSM-On-Prem.png)
## AWS SSM Managed Instances Activations
A managed instance is any Amazon EC2 instance or on-premises machine in your hybrid environment that has been configured for Systems Manager. Create activations for the required number of instances and note down the activation code and ID.
```sh
Activation Code   gVT8h+ROLaaXsNmR5sqo
Activation ID   a3dc1300-3356-4cff-8aa7-491a80c651f6
```
## Install SSM Client in On-Prem Server
```sh
mkdir -p /tmp/ssm
curl https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm -o /tmp/ssm/amazon-ssm-agent.rpm
sudo yum install -y /tmp/ssm/amazon-ssm-agent.rpm
sudo systemctl stop amazon-ssm-agent
sudo amazon-ssm-agent -register -code "gVT8h+ROLaaXsNmR5sqo" -id "a3dc1300-3356-4cff-8aa7-491a80c651f6" -region "ap-south-1" &
sudo systemctl start amazon-ssm-agent
```

_**Note:** In the Amazon EC2 console, however, your on-premises instances are distinguished from Amazon EC2 instances with the prefix "**mi-**"._


### Troubleshooting
The SSM Agent logs information in the following files. The information in these files can help you troubleshoot problems,
```sh
/var/log/amazon/ssm/amazon-ssm-agent.log
/var/log/amazon/ssm/errors.log
```




#### Describe Registration
```sh
aws ssm describe-instance-information --instance-information-filter-list key=InstanceIds,valueSet=mi-00722d1fcb2c55ef8
```



cat > SSMService-Trust.json << "EOF"
{
   "Version":"2012-10-17",
   "Statement":[
      {
         "Sid":"HybridSSM",
         "Effect":"Allow",
         "Principal":{
            "Service":[
               "ec2.amazonaws.com",
               "ssm.amazonaws.com"
            ]
         },
         "Action":"sts:AssumeRole"
      }
   ]
}
EOF

aws iam create-role --role-name SSMServiceRole --assume-role-policy-document file://SSMService-Trust.json


aws ssm create-activation --default-instance-name centos --iam-role SSMServiceRole --registration-limit 1 --region region ap-south-1


