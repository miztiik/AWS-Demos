#!/bin/bash
set -x -e

pubVPCID=$(aws ec2 create-vpc \
      --cidr-block 10.0.1.0/24 \
      --query 'Vpc.VpcId' \
	  --output text)

aws ec2 create-tags --resources "$pubVPCID" --tags 'Key=Name,Value=pubVPC'
	  

pvtVPCID=$(aws ec2 create-vpc \
      --cidr-block 10.0.2.0/24 \
      --query 'Vpc.VpcId' \
      --output text)

aws ec2 create-tags --resources "$pvtVPCID" --tags 'Key=Name,Value=pvtVPC'

### Enable DNS & Hostname support for our `pubVPC`
aws ec2 modify-vpc-attribute --vpc-id "$pubVPCID" --enable-dns-support "{\"Value\":true}"
aws ec2 modify-vpc-attribute --vpc-id "$pubVPCID" --enable-dns-hostnames "{\"Value\":true}"

### Create an internet gateway and assign it our public VPC
internetGatewayId=$(aws ec2 create-internet-gateway \
                  --query 'InternetGateway.InternetGatewayId' \
                  --output text)
aws ec2 attach-internet-gateway --internet-gateway-id "$internetGatewayId" --vpc-id "$pubVPCID"
aws ec2 create-tags --resources $internetGatewayId --tags 'Key=Name,Value=pubVPC-Internet-Gateway'

### Create the subnets for to spread the instances across multiple AZs
pubVPC_Subnet01ID=$(aws ec2 create-subnet --vpc-id "$pubVPCID" --cidr-block 10.0.1.0/25 --availability-zone us-east-1a --query 'Subnet.SubnetId' --output text)
pubVPC_Subnet02ID=$(aws ec2 create-subnet --vpc-id "$pubVPCID" --cidr-block 10.0.1.128/25 --availability-zone us-east-1b --query 'Subnet.SubnetId' --output text)

pvtVPC_Subnet01ID=$(aws ec2 create-subnet --vpc-id "$pvtVPCID" --cidr-block 10.0.2.0/25 --availability-zone us-east-1a --query 'Subnet.SubnetId' --output text)
pvtVPC_Subnet02ID=$(aws ec2 create-subnet --vpc-id "$pvtVPCID" --cidr-block 10.0.2.128/25 --availability-zone us-east-1b --query 'Subnet.SubnetId' --output text)

#### Tag the subnet ID's
aws ec2 create-tags --resources "$pubVPC_Subnet01ID" --tags 'Key=Name,Value=pubVPC_Subnet01-east-1a'
aws ec2 create-tags --resources "$pubVPC_Subnet02ID" --tags 'Key=Name,Value=pubVPC_Subnet02-east-1b'

aws ec2 create-tags --resources "$pvtVPC_Subnet01ID" --tags 'Key=Name,Value=pvtVPC_Subnet01-east-1a'
aws ec2 create-tags --resources "$pvtVPC_Subnet02ID" --tags 'Key=Name,Value=pvtVPC_Subnet02-east-1b'

### Create public routes and associate with internet gateway
routeTableID=$(aws ec2 create-route-table --vpc-id "$pubVPCID" --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id "$routeTableID" --destination-cidr-block 0.0.0.0/0 --gateway-id "$internetGatewayId"
aws ec2 associate-route-table --route-table-id "$routeTableID" --subnet-id "$pubVPC_Subnet01ID"
aws ec2 associate-route-table --route-table-id "$routeTableID" --subnet-id "$pubVPC_Subnet02ID"

### Creating a security group for the public instances
pubSecGrpID=$(aws ec2 create-security-group --group-name pubSecGrp \
            --description "Security Group for public instances" \
            --vpc-id "$pubVPCID" \
            --output text)
			
### Creating a security group for the private instances
pvtSecGrpID=$(aws ec2 create-security-group --group-name pvtSecGrp \
            --description "Security Group for private instances" \
            --vpc-id "$pvtVPCID" \
            --output text)


#### Add a rule that allows inbound SSH, HTTP, HTTP traffic ( from any source )
aws ec2 authorize-security-group-ingress --group-id "$pubSecGrpID" --protocol tcp --port 22 --cidr 0.0.0.0/0


### Create two EC2 Instances

##### Public Instances

pubInstanceID=$(aws ec2 run-instances \
           --image-id ami-2051294a \
           --count 1 \
           --instance-type t2.micro \
           --key-name kum-key \
           --security-group-ids "$pubSecGrpID" \
           --subnet-id "$pubVPC_Subnet01ID" \
           --associate-public-ip-address \
           --query 'Instances[0].InstanceId' \
           --output text)

pvtInstanceID=$(aws ec2 run-instances \
           --image-id ami-2051294a \
           --count 1 \
           --instance-type t2.micro \
           --key-name kum-key \
           --security-group-ids "$pvtSecGrpID" \
           --subnet-id "$pvtVPC_Subnet01ID" \
           --query 'Instances[0].InstanceId' \
           --output text)

pubInstanceUrl=$(aws ec2 describe-instances \
            --instance-ids "$pubInstanceID" \
            --query 'Reservations[0].Instances[0].PublicDnsName' \
            --output text)

##### Tag the instanes
aws ec2 create-tags --resources "$pubInstanceID" --tags 'Key=Name,Value=Public-Instance'
aws ec2 create-tags --resources "$pvtInstanceID" --tags 'Key=Name,Value=Private-Instance'
		   
# Create the VPC peering & accept the request
peerVPCID=$(aws ec2 create-vpc-peering-connection --vpc-id "$pubVPCID" --peer-vpc-id "$pvtVPCID" --query VpcPeeringConnection.VpcPeeringConnectionId --output text)
aws ec2 accept-vpc-peering-connection --vpc-peering-connection-id "$peerVPCID"
aws ec2 create-tags --resources "$peerVPCID" --tags 'Key=Name,Value=peer-VPC'

#### Adding the private VPC CIDR block to our public VPC route table as destination
aws ec2 create-route --route-table-id "$routeTableID" --destination-cidr-block 10.0.2.0/25 --vpc-peering-connection-id "$peerVPCID"
pvtRouteTableID=$(aws ec2 create-route-table --vpc-id "$pvtVPCID" --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id "$pvtRouteTableID" --destination-cidr-block 10.0.1.0/25 --vpc-peering-connection-id "$peerVPCID"
aws ec2 associate-route-table --route-table-id "$pvtRouteTableID" --subnet-id "$pvtVPC_Subnet01ID"

### Add a rule that allows inbound SSH (from our Public Instanes source)
aws ec2 authorize-security-group-ingress --group-id "$pvtSecGrpID" --protocol tcp --port 22 --cidr 10.0.1.0/24