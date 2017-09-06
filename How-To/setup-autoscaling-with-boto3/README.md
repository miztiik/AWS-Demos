# AWS 2 Tier Architecture setup with AWS CLI - Wordpress application on AWS RDS running MySQL
This demo assumes basic knowledge of AWS, Boto3 & Python.

**Prerequisites**:
 - AWS Account
 - IAM Role with Access & Secret Key
 - Boto3 Installed & Configured

At the end of the demo, we should be having an architecture as shown below,
![Setup Wordpress in AWS in 5 Minutes using Boto3](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/img/setup-ec2-wordpress-boto.png)


# Testing AutoScaling Workbench Results
```sh
[ec2-user]# yum -y install stress
stress --cpu 4 --timeout 300
```

```sh
[ec2-user]# poweroff
```




