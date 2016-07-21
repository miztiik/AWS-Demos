# AWS 2 Tier Architecture setup with AWS CLI - Wordpress application on AWS RDS running MySQL

Assuming you have already setup your AWS CLI, lets move forward;


### Creating a VPC
Lets create a `Virtual Private Cloud - VPC` for our setup with /16 range and get our VPC ID using the `query` parameter and set the output format to `text`. 

```sh
vpcID=$(aws ec2 create-vpc \
      --cidr-block 10.0.0.0/16 \
      --query 'Vpc.VpcId' \
      --output text)
```
##### Tag the VPC
Its is a good practice to give meaningful name to the AWS resources, Lets call our VPC `tmpVPC`
```sh
aws ec2 create-tags --resources $vpcID --tags 'Key=Name,Value=tmpVPC'
```
<sup>I have chosen /23 CIDR deliberately to allow us to create different subnets for our db and web instances. **Important:** _AWS reserves both the first four and the last IP address in each subnet's CIDR block. They're not available for use. The smallest subnet (and VPC) you can create uses a /28 netmask (16 IP addresses), and the largest uses a /16 netmask (65,536 IP addresses). Excellent resources to understand CIDR blocks [here](http://bradthemad.org/tech/notes/cidr_subnets.php) & [here](https://coderwall.com/p/ndm54w/creating-an-ec2-instance-in-a-vpc-with-the-aws-command-line-interface) & my quick help [gist](https://gist.github.com/miztiik/baecbaa67b1f10e38186d70e51c13a6c#file-cidr-ip-range)_<sup>



#### Creating subnets for the Database and Web Servers
Lets [reserve the IP Range](https://medium.com/aws-activate-startup-blog/practical-vpc-design-8412e1a18dcc#.dqxj9dlh2) to spread across multiple availability zones.

| 10.0.0.0/16 | IP Ranges     | Availability Zone |
|-------------|---------------|-------------------|
|             |  10.0.0.0/18  |        AZ A       |
|             |  10.0.64.0/18 |        AZ B       |
|             | 10.0.128.0/18 |        AZ C       |
|             | 10.0.192.0/18 |        None       |

```sh
10.0.0.0/16:
    10.0.0.0/18 - AZ A
        10.0.0.0/19 - Private (for DB in AZ)
        10.0.32.0/19
               10.0.32.0/20 - Public
               10.0.48.0/20 - Spare
    10.0.64.0/18 - AZ B
        10.0.64.0/19 - Private
        10.0.96.0/19
                10.0.96.0/20 - Public
                10.0.112.0/20 - Spare
    10.0.128.0/18 - AZ C
        10.0.128.0/19 - Private
        10.0.160.0/19
                10.0.160.0/20 - Public
                10.0.176.0/20 - Spare
    10.0.192.0/18 - Spare
```
_After creating all the subnets, It should look something like this,_
![alt tag](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/img/VPC-Subnet-AZ-Mapping.png)
 


```sh
webSubnetID=$(aws ec2 create-subnet \
           --vpc-id $vpcID \
           --cidr-block 10.0.1.0/28 \
           --availability-zone us-east-1d \
           --query 'Subnet.SubnetId' \
           --output text)
           
aws ec2 create-tags --resources $webSubnetID --tags 'Key=Name,Value=Web-Subnet'
```
<sup>**Important:** _[The RDS instances requires the db subnet group to span across (atleast two) availability zones](http://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_VPC.WorkingWithRDSInstanceinaVPC.html?shortFooter=true)_<sup>
```sh
dbSubnetID=$(aws ec2 create-subnet \
            --vpc-id $vpcID \
            --cidr-block 10.0.1.16/28 \
           --availability-zone us-east-1e \
            --query 'Subnet.SubnetId' \
            --output text)

aws ec2 create-tags --resources $dbSubnetID --tags 'Key=Name,Value=DB-Subnet'
```

Instances launched inside a VPC are invisible to the rest of the internet by default. AWS therefore does not bother assigning them a public DNS name. This can be changed easily by enabling the `DNS` support as shown below,

```sh
aws ec2 modify-vpc-attribute --vpc-id $vpcID --enable-dns-support "{\"Value\":true}"

aws ec2 modify-vpc-attribute --vpc-id $vpcID --enable-dns-hostnames "{\"Value\":true}"
```
_Check if internet gateway is set, If it wasn't there then do these,_
```sh 
internetGatewayId=$(aws ec2 create-internet-gateway --query 'InternetGateway.InternetGatewayId' --output text) && echo $internetGatewayId
aws ec2 attach-internet-gateway --internet-gateway-id $internetGatewayId --vpc-id $vpcID
```
##### Tag the Internet Gateway
```sh
aws ec2 create-tags --resources $internetGatewayId --tags 'Key=Name,Value=tmpVPC-Internet-Gateway'
```

#### Configuring the Route Table
Each subnet needs to have a route table associated with it to specify the routing of its outbound traffic. By default every subnet inherits the default VPC route table which allows for intra-VPC communication only.

The following adds a route table to our subnet that allows traffic not meant for an instance inside the VPC to be routed to the internet through our earlier created internet gateway.

```sh
routeTableID=$(aws ec2 create-route-table --vpc-id $vpcID --query 'RouteTable.RouteTableId' --output text)

aws ec2 associate-route-table --route-table-id $routeTableID --subnet-id $webSubnetID

aws ec2 create-route --route-table-id $routeTableID --destination-cidr-block 0.0.0.0/0 --gateway-id $internetGatewayId
```

### Creating a security group for the Web Servers
 - Group Name - `webSecGrp`
 - Description - `My Web Security Group`

```sh
webSecGrpID=$(aws ec2 create-security-group --group-name webSecGrp \
            --description "My Security Group for web servers" \
            --vpc-id $vpcID \
            --output text)
```

#### Add a rule that allows inbound SSH, HTTP, HTTP traffic ( from any source )

Incase you want to confirm yor security group to be sure, To describe a security group for EC2-VPC, `aws ec2 describe-security-groups --group-ids $webSecGrpID`

```sh
aws ec2 authorize-security-group-ingress --group-id ${webSecGrpID} --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id ${webSecGrpID} --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id ${webSecGrpID} --protocol tcp --port 443 --cidr 0.0.0.0/0
```
_Interesting reading here about why we need to use security group ID instead of name; [AWS Documentation](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-network-security.html) & [Github Bug Report](https://github.com/hashicorp/terraform/issues/575)_

>When you specify a security group for a nondefault VPC to the CLI or the API actions, you must use the security group ID and not the >security group name to identify the security group.


### Creating a Security Group for RDS Database (running MySQL)
 - Group Name - `dbSecGrp`
 - Description - `My Database Security Group`

```sh
dbSecGrpID=$(aws ec2 create-security-group --group-name dbSecGrp --description "My Database Group for web servers" --vpc-id $vpcID --output text)
```

#### Add a rule that allows inbound MySQL from Webservers (in our Web Security Group)

```sh
aws ec2 authorize-security-group-ingress \
        --group-id ${dbSecGrpID} \
        --protocol tcp \
        --port 3306 \
        --source-group \
        ${webSecGrpID}
```

#### Creating the RDS - MySQL Instance
```sh

        --db-security-groups $webSecGrpID $dbSecGrpID \
aws rds create-db-instance \
        --db-instance-identifier rds-mysql-inst01 \
        --allocated-storage 5 \
        --db-instance-class db.t2.micro \
        --no-multi-az \
        --availability-zone us-east-1e \
        --vpc-security-group-ids $dbSecGrpID \
        --db-subnet-group-name "DBSubnet" \
        --no-auto-minor-version-upgrade \
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


#### Launch an instance in your public subnet
```sh
instanceID=$(aws ec2 run-instances \
           --image-id ami-ecd5e884 \
           --count 1 \
           --instance-type t2.micro \
           --key-name ec2-dev \
           --security-group-ids $securityGroupId \
           --subnet-id $webSubnetID \
           --associate-public-ip-address \
           --query 'Instances[0].InstanceId' \
           --output text)

instanceUrl=$(aws ec2 describe-instances \
            --instance-ids $instanceID \
            --query 'Reservations[0].Instances[0].PublicDnsName' \
            --output text)
```







