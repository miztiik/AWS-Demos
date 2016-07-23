# AWS 2 Tier Architecture setup with AWS CLI - Wordpress application on AWS RDS running MySQL

There are two parts to the setup,
- **Part 1** - Setting up the network infrastructure (VPC, Subnets, Security Groups)
- **Part 2** - Creating & Configure the Database, Web & Load Balancer Instances

Assuming you have already setup your AWS CLI for Region `US East (N. Virginia)`. Lets move forward;

# Part 1 - Create VPC, Subnet, Security Group
### Setting the AWS Region
```sh
export AWS_DEFAULT_REGION=us-east-1
```

### Creating a VPC
Lets create a `Virtual Private Cloud - VPC` for our setup with /20 range and get our VPC ID using the `query` parameter and set the output format to `text`. Its is a good practice to give meaningful name to the AWS resources, Lets call our VPC `tmpVPC`

```sh
vpcID=$(aws ec2 create-vpc \
      --cidr-block 10.0.0.0/20 \
      --query 'Vpc.VpcId' \
      --output text)
```
##### Tag the VPC
```sh
aws ec2 create-tags --resources "$vpcID" --tags 'Key=Name,Value=tmpVPC'
```

Instances launched inside a VPC are invisible to the rest of the internet by default. AWS therefore does not bother assigning them a public DNS name. This can be changed easily by enabling the `DNS` support as shown below,

```sh
aws ec2 modify-vpc-attribute --vpc-id "$vpcID" --enable-dns-support "{\"Value\":true}"

aws ec2 modify-vpc-attribute --vpc-id "$vpcID" --enable-dns-hostnames "{\"Value\":true}"
```

_Check if internet gateway is set. If it wasn't there then do these,_
```sh 
internetGatewayId=$(aws ec2 create-internet-gateway \
                  --query 'InternetGateway.InternetGatewayId' \
                  --output text) && echo "$internetGatewayId"
aws ec2 attach-internet-gateway --internet-gateway-id "$internetGatewayId" --vpc-id "$vpcID"
```

##### Tag the Internet Gateway

```sh
aws ec2 create-tags --resources $internetGatewayId --tags 'Key=Name,Value=tmpVPC-Internet-Gateway'
```

<sup>I have chosen /20 CIDR deliberately to allow us to create different subnets for our db, web instances and reserve some for the future. You might want to choose something else that works better for you. **Important:** _AWS reserves both the first four and the last IP address in each subnet's CIDR block. They're not available for use. The smallest subnet (and VPC) you can create uses a /28 netmask (16 IP addresses), and the largest uses a /16 netmask (65,536 IP addresses). Excellent resources to understand CIDR blocks [here](http://bradthemad.org/tech/notes/cidr_subnets.php) & [here](https://coderwall.com/p/ndm54w/creating-an-ec2-instance-in-a-vpc-with-the-aws-command-line-interface) & my quick help [gist](https://gist.github.com/miztiik/baecbaa67b1f10e38186d70e51c13a6c#file-cidr-ip-range)_<sup>



## Subnet Reservation for the Database, Web Servers & future
Lets [reserve the IP Range](https://medium.com/aws-activate-startup-blog/practical-vpc-design-8412e1a18dcc#.dqxj9dlh2) to spread across multiple availability zones.

| VPC Range   | Availability Zone | Reservation Purpose | IP Ranges   | IP Ranges    | IP Ranges    |
|-------------|-------------------|---------------------|-------------|--------------|--------------|
| 10.0.0.0/20 |                   |                     |             |              |              |
|             | AZ1               | US-East-1b          | 10.0.0.0/21 |              |              |
|             | AZ1               | Private - DB Subnet |             |  10.0.0.0/22 |              |
|             | AZ1               |                     |             |  10.0.4.0/22 |              |
|             | AZ1               | Web Subnet          |             |              |  10.0.4.0/23 |
|             | AZ1               | Spare Subnet        |             |              |  10.0.6.0/23 |
|             |                   |                     |             |              |              |
|             | AZ2               | US-East-1c          | 10.0.8.0/21 |              |              |
|             | AZ2               | Private - DB Subnet |             |  10.0.8.0/22 |              |
|             | AZ2               |                     |             | 10.0.12.0/22 |              |
|             | AZ2               | Web Subnet          |             |              | 10.0.12.0/23 |
|             | AZ2               | Spare Subnet        |             |              | 10.0.14.0/23 |
       
_After creating all the subnets, It should look something like this,_
![alt tag](https://github.com/miztiik/AWS-Demos/blob/master/img/VPC-Subnet-AZ%5B1-2%5D-Mapping.png)
 


### Creating subnets for the DB & Web Servers in AZ1
```sh
USEast1b_DbSubnetID=$(aws ec2 create-subnet --vpc-id "$vpcID" --cidr-block 10.0.0.0/22 --availability-zone us-east-1b --query 'Subnet.SubnetId' --output text)

USEast1b_WebSubnetID=$(aws ec2 create-subnet --vpc-id "$vpcID" --cidr-block 10.0.4.0/23 --availability-zone us-east-1b --query 'Subnet.SubnetId' --output text)

USEast1b_SpareSubnetID=$(aws ec2 create-subnet --vpc-id "$vpcID" --cidr-block 10.0.6.0/23 --availability-zone us-east-1b --query 'Subnet.SubnetId' --output text)
```

##### Tag the subnet ID's for AZ1
```sh

aws ec2 create-tags --resources "$USEast1b_DbSubnetID" --tags 'Key=Name,Value=az1-us-east-1b-DB-Subnet'

aws ec2 create-tags --resources "$USEast1b_WebSubnetID" --tags 'Key=Name,Value=az1-us-east-1b-Web-Subnet'

aws ec2 create-tags --resources "$USEast1b_SpareSubnetID" --tags 'Key=Name,Value=az1-us-east-1b-Spare-Subnet'

```

### Creating subnets for the DB & Web Servers in AZ2
```sh
USEast1c_DbSubnetID=$(aws ec2 create-subnet --vpc-id "$vpcID" --cidr-block 10.0.8.0/22 --availability-zone us-east-1c --query 'Subnet.SubnetId' --output text)

USEast1c_WebSubnetID=$(aws ec2 create-subnet --vpc-id "$vpcID" --cidr-block 10.0.12.0/23 --availability-zone us-east-1c --query 'Subnet.SubnetId' --output text)

USEast1c_SpareSubnetID=$(aws ec2 create-subnet --vpc-id "$vpcID" --cidr-block 10.0.14.0/23 --availability-zone us-east-1c --query 'Subnet.SubnetId' --output text)
```
##### Tag the subnet ID's for AZ2
```sh
aws ec2 create-tags --resources "$USEast1c_DbSubnetID" --tags 'Key=Name,Value=az1-us-east-1c-DB-Subnet'

aws ec2 create-tags --resources "$USEast1c_WebSubnetID" --tags 'Key=Name,Value=az1-us-east-1c-Web-Subnet'

aws ec2 create-tags --resources "$USEast1c_SpareSubnetID" --tags 'Key=Name,Value=az1-us-east-1c-Spare-Subnet'
```

### Configuring the Route Table
Each subnet needs to have a route table associated with it to specify the routing of its outbound traffic. By default every subnet inherits the default VPC route table which allows for intra-VPC communication only.

The following adds a route table to our subnet that allows traffic not meant for an instance inside the VPC to be routed to the internet through our earlier created internet gateway.

```sh
routeTableID=$(aws ec2 create-route-table --vpc-id "$vpcID" --query 'RouteTable.RouteTableId' --output text)

aws ec2 create-route --route-table-id "$routeTableID" --destination-cidr-block 0.0.0.0/0 --gateway-id "$internetGatewayId"

aws ec2 associate-route-table --route-table-id "$routeTableID" --subnet-id "$USEast1b_WebSubnetID"

aws ec2 associate-route-table --route-table-id "$routeTableID" --subnet-id "$USEast1c_WebSubnetID"
```

### Creating a security group for the Web Servers
 - Group Name - `webSecGrp`
 - Description - `My Web Security Group`

```sh
webSecGrpID=$(aws ec2 create-security-group --group-name webSecGrp \
            --description "Security Group for Web servers" \
            --vpc-id "$vpcID" \
            --output text)
```

#### Add a rule that allows inbound SSH, HTTP, HTTP traffic ( from any source )

```sh
aws ec2 authorize-security-group-ingress --group-id "$webSecGrpID" --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id "$webSecGrpID" --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id "$webSecGrpID" --protocol tcp --port 443 --cidr 0.0.0.0/0
```
_Interesting reading here about why we need to use security group ID instead of name; [AWS Documentation](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-network-security.html) & [Github Bug Report](https://github.com/hashicorp/terraform/issues/575)_

>When you specify a security group for a nondefault VPC to the CLI or the API actions, you must use the security group ID and not the security group name to identify the security group.

# Creating the RDS Instance
## Pre-Requisites
- DB Subnet - _[The RDS instances requires the db subnet group to span across (atleast two) availability zones](http://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html?shortFooter=true)_
 - DB Security Group - _Security group all allows other EC2  instances to connect with this RDS instance_

### Create the `DB Subnet`
```sh
aws rds create-db-subnet-group \
        --db-subnet-group-name "mysqlDBSubnet" \
        --db-subnet-group-description "Subnet group for my databases instances" \
        --subnet-ids "$USEast1b_DbSubnetID" "$USEast1c_DbSubnetID"
```

#### Creating a Security Group for RDS Database (running MySQL)
 - Group Name - `dbSecGrp`
 - Description - `My Database Security Group`

```sh
dbSecGrpID=$(aws ec2 create-security-group \
           --group-name dbSecGrp \
           --description "Security Group for database servers" \
           --vpc-id "$vpcID" \
           --output text)
```

#### Add a rule that allows inbound MySQL from Webservers (in our Web Security Group)

```sh
aws ec2 authorize-security-group-ingress \
        --group-id "$dbSecGrpID" \
        --protocol tcp \
        --port 3306 \
        --source-group \
        "$webSecGrpID"
```
# Part 2 - Creating & Configure the Database, Web & Load Balancer Instances
### Creating the RDS - MySQL Instance
Creates a new DB subnet group. DB subnet groups must contain at least one subnet in at least two AZs in the region.
```sh
aws rds create-db-instance \
        --db-instance-identifier rds-mysql-inst01 \
        --allocated-storage 5 \
        --db-instance-class db.t2.micro \
        --no-multi-az \
        --no-auto-minor-version-upgrade \
        --availability-zone us-east-1b \
        --vpc-security-group-ids "$dbSecGrpID" \
        --db-subnet-group-name "mysqldbsubnet" \
        --engine mysql \
        --port 3306 \
        --master-username dbuser \
        --master-user-password dbuserpass \
        --db-name wpdb \
        --backup-retention-period 3
```

_**Refer:**_ 
- [1] https://www.linux.com/blog/introduction-aws-command-line-tool-part-2
- [2] http://docs.aws.amazon.com/cli/latest/reference/rds/create-db-instance.html
- [3] [Cloning RDS Instances for Testing](http://blog.dmcquay.com/devops/2015/09/18/cloning-rds-instances-for-testing.html)

##### Create a DB parameter group to monitor CRUD
```sh
aws rds create-db-parameter-group \
    --db-parameter-group-name myParamGrp \
    --db-parameter-group-family MySQL5.6 \
    --description "My new parameter group"

aws rds modify-db-instance --db-instance-identifier rds-mysql-inst01 --db-parameter-group-name myParamGrp

aws rds modify-db-parameter-group --db-parameter-group-name myParamGrp --parameters "ParameterName=general_log, ParameterValue=ON, Description=logParameter,ApplyMethod=immediate"
```





```sh
aws ec2 create-key-pair --key-name webKey --query 'KeyMaterial' --output text > webKey.pem
chmod 400 webKey.pem

cat >> userDataScript <<EOF
#!/bin/bash
set -e -x

# Setting up the HTTP server 
yum update -y
yum install -y httpd php php-mysql mysql
service httpd start
chkconfig httpd on
groupadd www
usermod -a -G www ec2-user


# Download wordpress site & move to http
cd /var/www/
wget https://wordpress.org/latest.tar.gz && tar -zxf latest.tar.gz
rm -rf /var/www/html
mv wordpress /var/www/html

# Set the permissions
chown -R root:www /var/www
chmod 2775 /var/www
find /var/www -type d -exec chmod 2775 {} +
find /var/www -type f -exec chmod 0664 {} +
echo "<?php phpinfo(); ?>" > /var/www/html/phpinfo.php
EOF
```
### Create the Web Servers
```sh
instanceID=$(aws ec2 run-instances \
           --image-id ami-2051294a \
           --count 1 \
           --instance-type t2.micro \
           --key-name webKey \
           --security-group-ids "$webSecGrpID" \
           --subnet-id "$webSubnetID" \
           --user-data file://userDataScript \
           --associate-public-ip-address \
           --query 'Instances[0].InstanceId' \
           --output text)
           
instanceUrl=$(aws ec2 describe-instances \
            --instance-ids "$instanceID" \
            --query 'Reservations[0].Instances[0].PublicDnsName' \
            --output text)

# Get the IP address of the running instance:
ip_address=$(aws ec2 describe-instances \
           --instance-ids "$instanceID" \
           --output text --query 'Reservations[*].Instances[*].PublicIpAddress')
           ```

### Create the Elastic Load Balancer
_**Ref:**_ https://aws.amazon.com/articles/1636185810492479

aws elb create-load-balancer \
--load-balancer-name my-load-balancer \
--listeners "Protocol=HTTP,LoadBalancerPort=80,InstanceProtocol=HTTP,InstancePort=80" \
--subnets "$webSubnetID" \
--security-groups "$webSecGrpID"





