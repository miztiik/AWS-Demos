#!/bin/bash
set -x
set -e

# Setting the Region
prefAZ=us-east-1
export AWS_DEFAULT_REGION="$prefAZ"

# Creating a VPC

vpcID=$(aws ec2 create-vpc \
      --cidr-block 10.0.0.0/20 \
      --query 'Vpc.VpcId' \
      --output text)

# Tag the VPC

aws ec2 create-tags --resources "$vpcID" --tags 'Key=Name,Value=tmpVPC'

# Enable DNS & Hostname support
aws ec2 modify-vpc-attribute --vpc-id "$vpcID" --enable-dns-support "{\"Value\":true}"
aws ec2 modify-vpc-attribute --vpc-id "$vpcID" --enable-dns-hostnames "{\"Value\":true}"

# Check if internet gateway is set, If it wasn't there then do these,
internetGatewayId=$(aws ec2 create-internet-gateway \
                  --query 'InternetGateway.InternetGatewayId' \
                  --output text) && echo "$internetGatewayId"
aws ec2 attach-internet-gateway --internet-gateway-id "$internetGatewayId" --vpc-id "$vpcID"
aws ec2 create-tags --resources $internetGatewayId --tags 'Key=Name,Value=tmpVPC-Internet-Gateway'


# Creating subnets for the DB & Web Servers in Multiple AZ1

USEast1b_DbSubnetID=$(aws ec2 create-subnet --vpc-id "$vpcID" --cidr-block 10.0.0.0/22 --availability-zone us-east-1b --query 'Subnet.SubnetId' --output text)
USEast1b_WebSubnetID=$(aws ec2 create-subnet --vpc-id "$vpcID" --cidr-block 10.0.4.0/23 --availability-zone us-east-1b --query 'Subnet.SubnetId' --output text)
USEast1b_SpareSubnetID=$(aws ec2 create-subnet --vpc-id "$vpcID" --cidr-block 10.0.6.0/23 --availability-zone us-east-1b --query 'Subnet.SubnetId' --output text)

# Tag the subnet ID's for AZ1
aws ec2 create-tags --resources "$USEast1b_DbSubnetID" --tags 'Key=Name,Value=az1-us-east-1b-DB-Subnet'
aws ec2 create-tags --resources "$USEast1b_WebSubnetID" --tags 'Key=Name,Value=az1-us-east-1b-Web-Subnet'
aws ec2 create-tags --resources "$USEast1b_SpareSubnetID" --tags 'Key=Name,Value=az1-us-east-1b-Spare-Subnet'

# Creating subnets for the DB & Web Servers in Multiple AZ2
USEast1c_DbSubnetID=$(aws ec2 create-subnet --vpc-id "$vpcID" --cidr-block 10.0.8.0/22 --availability-zone us-east-1c --query 'Subnet.SubnetId' --output text)
USEast1c_WebSubnetID=$(aws ec2 create-subnet --vpc-id "$vpcID" --cidr-block 10.0.12.0/23 --availability-zone us-east-1c --query 'Subnet.SubnetId' --output text)
USEast1c_SpareSubnetID=$(aws ec2 create-subnet --vpc-id "$vpcID" --cidr-block 10.0.14.0/23 --availability-zone us-east-1c --query 'Subnet.SubnetId' --output text)

# Tag the subnet ID's for AZ2
aws ec2 create-tags --resources "$USEast1c_DbSubnetID" --tags 'Key=Name,Value=az1-us-east-1c-DB-Subnet'
aws ec2 create-tags --resources "$USEast1c_WebSubnetID" --tags 'Key=Name,Value=az1-us-east-1c-Web-Subnet'
aws ec2 create-tags --resources "$USEast1c_SpareSubnetID" --tags 'Key=Name,Value=az1-us-east-1c-Spare-Subnet'


# Configuring the Route Table
routeTableID=$(aws ec2 create-route-table --vpc-id "$vpcID" --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id "$routeTableID" --destination-cidr-block 0.0.0.0/0 --gateway-id "$internetGatewayId"
aws ec2 associate-route-table --route-table-id "$routeTableID" --subnet-id "$USEast1b_WebSubnetID"
aws ec2 associate-route-table --route-table-id "$routeTableID" --subnet-id "$USEast1c_WebSubnetID"


# Creating a security group for the Web Servers
webSecGrpID=$(aws ec2 create-security-group --group-name webSecGrp \
            --description "Security Group for Web servers" \
            --vpc-id "$vpcID" \
            --output text)

# Add a rule that allows inbound SSH, HTTP, HTTP traffic ( from any source )
aws ec2 authorize-security-group-ingress --group-id "$webSecGrpID" --protocol tcp --port 22 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id "$webSecGrpID" --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id "$webSecGrpID" --protocol tcp --port 443 --cidr 0.0.0.0/0


# Creating a subnet for the DB instances in RDS
aws rds create-db-subnet-group \
        --db-subnet-group-name "mysqlDBSubnet" \
        --db-subnet-group-description "Subnet group for my databases instances" \
        --subnet-ids "$USEast1b_DbSubnetID" "$USEast1c_DbSubnetID"

# Creating a Security Group for Database RDS - MySQL from Web Security Group
dbSecGrpID=$(aws ec2 create-security-group \
           --group-name dbSecGrp \
           --description "Security Group for database servers" \
           --vpc-id "$vpcID" \
           --output text)


# Add a rule that allows inbound MySQL ( from any source )
aws ec2 authorize-security-group-ingress \
        --group-id "$dbSecGrpID" \
        --protocol tcp \
        --port 3306 \
        --source-group \
        "$webSecGrpID"


### Create a DB parameter group to monitor CRUD
aws rds create-db-parameter-group \
    --db-parameter-group-name myParamGrp \
    --db-parameter-group-family MySQL5.6 \
    --description "My new parameter group"

aws rds modify-db-parameter-group --db-parameter-group-name myParamGrp --parameters "ParameterName=general_log, ParameterValue=ON, Description=logParameter,ApplyMethod=immediate"


### Creating the RDS - MySQL Instance

rdsInstID=rds-mysql-inst01
aws rds create-db-instance \
        --db-instance-identifier "$rdsInstID" \
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
        --db-parameter-group-name myParamGrp \
        --db-name wpdb \
        --backup-retention-period 3
        
aws rds modify-db-instance --db-instance-identifier "$rdsInstID" --db-parameter-group-name myParamGrp


# mysql -h rds-mysql-inst01.cslmvkhlku4b.us-east-1.rds.amazonaws.com -P 3306 -u dbuser -p



# Set the key to connect to the web server EC2 Instances
aws ec2 delete-key-pair --key-name wpKey
aws ec2 create-key-pair --key-name wpKey --query 'KeyMaterial' --output text > wpKey.pem
chmod 400 wpKey.pem

cat >> userDataScript <<EOF
#!/bin/bash
set -e -x

# Setting up the HTTP server 
yum update -y
yum install -y httpd php php-mysql mysql
service httpd start
chkconfig httpd on
groupadd www
	


# Download wordpress site & move to http
cd /var/www/
curl -O https://wordpress.org/latest.tar.gz && tar -zxf latest.tar.gz
rm -rf /var/www/html
mv wordpress /var/www/html

# Set the permissions
chown -R root:www /var/www
chmod 2775 /var/www
find /var/www -type d -exec chmod 2775 {} +
find /var/www -type f -exec chmod 0664 {} +

# SE Linux permissive
setsebool -P httpd_can_network_connect=1
setsebool httpd_can_network_connect_db on

systemctl restart httpd
echo "<?php phpinfo(); ?>" > /var/www/html/phpinfo.php
EOF

instanceID=$(aws ec2 run-instances \
           --image-id ami-2051294a \
           --count 1 \
           --instance-type t2.micro \
           --key-name wpKey \
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


# Create the load balancers
aws elb create-load-balancer \
--load-balancer-name wpELB \
--listeners "Protocol=HTTP,LoadBalancerPort=80,InstanceProtocol=HTTP,InstancePort=80" \
--availability-zones "$prefAZ" \
--subnets "$USEast1c_WebSubnetID" "$USEast1b_WebSubnetID" \
--security-groups "$webSecGrpID" \
--tags 'Key=Name,Value=wpELB'

## Register the EC2 Instances to our Load Balance
aws elb register-instances-with-load-balancer --load-balancer-name wpELB --instances "$instanceID"



# Create DB Snapshot
aws rds describe-db-snapshots --db-instance-identifier $rdsInstID"
aws rds describe-db-snapshots --db-instance-identifier rds-mysql-inst01

# Backup of the WP-Site-DB
# mysqldump -Q --add-drop-table -u dbuser -p -h rds-mysql-inst01.cslmvkhlku4b.us-east-1.rds.amazonaws.com wpdb > dbdump.sql | gzip | s3cmd put - s3://bucket/aws-demo-work
# 	

# Deletion of all resources
# aws elb delete-load-balancer --load-balancer-name wpELB
# aws ec2 terminate-instances --instance-ids "$instanceID"
# aws rds delete-db-instance --db-instance-identifier "$rdsInstID" --skip-final-snapshot
# aws rds delete-db-subnet-group --db-subnet-group-name "mysqlDBSubnet"
# aws rds delete-db-parameter-group --db-parameter-group-name "myParamGrp"