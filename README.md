# AWS 2 Tier Architecture setup with AWS CLI - Wordpress application on AWS RDS running MySQL

Assuming you have already setup your AWS CLI, lets move forward;


### Creating a VPC
Lets create a `Virtual Private Cloud - VPC` for our setup with 512 IPs and get our VPC ID using the `query` parameter and set the output format to `text`. 

```sh
vpcID=$(aws ec2 create-vpc \
      --cidr-block 10.0.0.0/23 \
      --query 'Vpc.VpcId' \
      --output text)
```
##### Tag the VPC
Its is a good practice to give meaningful name to the AWS resources, Lets call our VPC `tmpVPC`
```sh
aws ec2 create-tags --resources $vpcID --tags 'Key=Name,Value=tmpVPC'
```
<sup>I have chosen /23 CIDR deliberately to allow us to create different subnets for our db and web instances. **Important:** _AWS reserves both the first four and the last IP address in each subnet's CIDR block. They're not available for use. The smallest subnet (and VPC) you can create uses a /28 netmask (16 IP addresses), and the largest uses a /16 netmask (65,536 IP addresses)._ Excellent resource to understand [CIDR blocks](http://bradthemad.org/tech/notes/cidr_subnets.php) & [here](https://coderwall.com/p/ndm54w/creating-an-ec2-instance-in-a-vpc-with-the-aws-command-line-interface)<sup>

#### Creating subnets for the Database and Web Servers
Lets reserve the IP Range `10.0.1.0 - 10.0.1.15` for Web Servers & IP Ranges `10.0.1.16 - 10.0.1.31` for Database Servers
```sh
webSubnetID=$(aws ec2 create-subnet \
           --vpc-id $vpcID \
           --cidr-block 10.0.1.0/28 \
           --query 'Subnet.SubnetId' \
           --output text)
           
aws ec2 create-tags --resources $webSubnetID --tags 'Key=Name,Value=WebSubnet'

dbSubnetID=$(aws ec2 create-subnet \
            --vpc-id $vpcID \
            --cidr-block 10.0.1.16/28 \
            --query 'Subnet.SubnetId' --output text)

aws ec2 create-tags --resources $dbSubnetID --tags 'Key=Name,Value=DBSubnet'
```

Instances launched inside a VPC are invisible to the rest of the internet by default. AWS therefore does not bother assigning them a public DNS name. This can be changed easily by enabling the `DNS` support as shown below,

```sh
aws ec2 modify-vpc-attribute --vpc-id $vpcID --enable-dns-support "{\"Value\":true}"

aws ec2 modify-vpc-attribute --vpc-id $vpcID --enable-dns-hostnames "{\"Value\":true}"
```
_Check if internet gateway is set, If it wasn't there then do these,_
```sh 
intGatewayID=$(aws ec2 create-internet-gateway --output text)
aws ec2 attach-internet-gateway --vpc-id $vpcID --internet-gateway-id "$intGatewayID"
```

#### Configuring the Route Table
Each subnet needs to have a route table associated with it to specify the routing of its outbound traffic. By default every subnet inherits the default VPC route table which allows for intra-VPC communication only.

The following adds a route table to our subnet that allows traffic not meant for an instance inside the VPC to be routed to the internet through our earlier created internet gateway.

```sh
routeTableID=$(aws ec2 create-route-table --vpc-id $vpcID --query 'RouteTable.RouteTableId' --output text)

aws ec2 associate-route-table --route-table-id $routeTableID --subnet-id $subnetId

aws ec2 create-route --route-table-id $routeTableID --destination-cidr-block 0.0.0.0/0 --gateway-id $iGatewayID
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
aws ec2 authorize-security-group-ingress --group-id ${webSecGrpID} --protocol tcp --port 22 --cidr 0.0.0.0/28
aws ec2 authorize-security-group-ingress --group-id ${webSecGrpID} --protocol tcp --port 80 --cidr 0.0.0.0/28
aws ec2 authorize-security-group-ingress --group-id ${webSecGrpID} --protocol tcp --port 443 --cidr 0.0.0.0/28
```
_Interesting read here about why we need to use security group ID instead of name; [AWS Documentation](http://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-network-security.html) & [Github Bug Report](https://github.com/hashicorp/terraform/issues/575)_

>When you specify a security group for a nondefault VPC to the CLI or the API actions, you must use the security group ID and not the >security group name to identify the security group.


### Creating a Security Group for Database RDS - MySQL from Web Security Group
 - Group Name - `dbSecGrp`
 - Description - `My Database Security Group`


```sh
dbSecGrpID=$(aws ec2 create-security-group --group-name dbSecGrp --description "My Database Group for web servers" --vpc-id $vpcID --output text)
```

#### Add a rule that allows inbound MySQL ( from any source )

```sh
aws ec2 authorize-security-group-ingress --group-id ${dbSecGrpID} --protocol tcp --port 3306 --source-group ${webSecGrpID}
```

#### Creating the RDS - MySQL Instance
```sh
aws rds create-db-instance \
--db-instance-identifier rds-mysql-inst01 \
--allocated-storage 5 \
--db-instance-class t2.micro \
--engine mysql \
--master-username dbuser \
--master-user-password dbuserpass
--backup-retention-period 3
```


#### Launch an instance in your public subnet
```sh
aws ec2 run-instances --image-id ami-a4827dc9 --count 1 --instance-type t2.micro --key-name MyKeyPair --security-group-ids sg-e1fb8c9a --subnet-id subnet-b46032ec
```







