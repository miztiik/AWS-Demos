# AWS 2 Tier Architecture setup with AWS CLI - Wordpress application on AWS RDS running MySQL

Assuming you have already setup your AWS CLI, lets move forward;


### Create a VPC
Lets create a `Virtual Private Cloud - VPC` for our setup with 16 IPs and get our VPC ID using the `query` parameter and set the output format to `text`. 

<sup>Excellent resource to understand [CIDR blocks](http://bradthemad.org/tech/notes/cidr_subnets.php) & [here](https://coderwall.com/p/ndm54w/creating-an-ec2-instance-in-a-vpc-with-the-aws-command-line-interface)<sup>


`vpcID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/28 --query 'Vpc.VpcId' --output text)`



### Creating a security group for the Web Servers
 - Group Name - `webSecGrp`
 - Description - `My Web Security Group`

`webSecGrpID=$(aws ec2 create-security-group --group-name webSecGrp --description "My Security Group for web servers" --vpc-id $vpcID --output text)`


Instances launched inside a VPC are invisible to the rest of the internet by default. AWS therefore does not bother assigning them a public DNS name. This can be changed easily,

```
aws ec2 modify-vpc-attribute --vpc-id $vpcID --enable-dns-support "{\"Value\":true}"

aws ec2 modify-vpc-attribute --vpc-id $vpcID --enable-dns-hostnames "{\"Value\":true}"
```

#### Add a rule that allows inbound SSH, HTTP, HTTP traffic ( from any source )

Incase you want to confirm yor security group to be sure, To describe a security group for EC2-VPC, `aws ec2 describe-security-groups --group-ids $webSecGrpID`

```sh
aws ec2 authorize-security-group-ingress --group-id ${webSecGrpID} --protocol tcp --port 22 --cidr 0.0.0.0/28
aws ec2 authorize-security-group-ingress --group-id ${webSecGrpID} --protocol tcp --port 80 --cidr 0.0.0.0/28
aws ec2 authorize-security-group-ingress --group-id ${webSecGrpID} --protocol tcp --port 443 --cidr 0.0.0.0/28
```
_Interesting read here about why we need to use security group ID instead of name; [AWS Documentation](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-network-security.html) & [Github Bug Report](https://github.com/hashicorp/terraform/issues/575)_

>When you specify a security group for a nondefault VPC to the CLI or the API actions, you must use the security group ID and not the >security group name to identify the security group.


### Creating a Security Group for Database RDS - MySQL from Web Security Group
 - Group Name - `dbSecGrp`
 - Description - `My Database Security Group`


`dbSecGrpID=$(aws ec2 create-security-group --group-name dbSecGrp --description "My Database Group for web servers" --vpc-id $vpcID --output text)`

#### Add a rule that allows inbound MySQL ( from any source )

`aws ec2 authorize-security-group-ingress --group-id ${dbSecGrpID} --protocol tcp --port 3306 --source-group ${webSecGrpID}`
