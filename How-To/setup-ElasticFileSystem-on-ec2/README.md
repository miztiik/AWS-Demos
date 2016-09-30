# Create Amazon EFS File System and Mount It on EC2 Instance(s)

## Why you need EFS File System?
Suppose you have one or more EC2 instances launched in your VPC. Now you want to create and share a file system on these instances, EFS is your friend. You can mount an Amazon EFS file system on EC2 instances in your Amazon Virtual Private Cloud (Amazon VPC) using the Network File System version 4.1 protocol (NFSv4.1). Amazon EFS provides elastic, shared file storage that is
 - **POSIX-compliant**
 - Supports **concurrent read and write access** from multiple Amazon EC2 instances
 - Accessible from all of the `Availability Zones` in the `AWS Region`

Having said that, Beware of some of the _[not supported features of EFS](http://docs.aws.amazon.com/efs/latest/ug/nfs4-unsupported-features.html)_.



In this walkthrough, you will create the following resources:
 - Amazon EC2 resources - 
   - Two security groups (for your EC2 instance and Amazon EFS file system) - You add rules to these security groups to authorize appropriate inbound/outbound access to allow your EC2 instance to connect to the file system via the mount target using a standard NFSv4.1 TCP port.
   - An Amazon EC2 instance in your VPC.
 - Amazon EFS resources:
   - A file system.
   - A mount target for your file system - To mount your file system on an EC2 instance you need to create a mount target in your VPC. You can create one mount target in each of the Availability Zones in your VPC. 

## Creating EC2 Resources

### Create the VPC
Lets create a /24 VPC and tag it `pubVPC` along with the interget gateway

```sh
# Setting the Region
prefAZ=us-west-1
export AWS_DEFAULT_REGION="$prefAZ"

pubVPCID=$(aws ec2 create-vpc \
           --cidr-block 10.0.1.0/24 \
           --query 'Vpc.VpcId' \
           --output text)
           
aws ec2 create-tags --resources "$pubVPCID" --tags 'Key=Name,Value=pubVPC'

### Enable DNS & Hostname support for our `pubVPC`
aws ec2 modify-vpc-attribute --vpc-id "$pubVPCID" --enable-dns-support "{\"Value\":true}"
aws ec2 modify-vpc-attribute --vpc-id "$pubVPCID" --enable-dns-hostnames "{\"Value\":true}"

### Create an internet gateway and assign it our public VPC
internetGatewayId=$(aws ec2 create-internet-gateway \
                  --query 'InternetGateway.InternetGatewayId' \
                  --output text)
aws ec2 attach-internet-gateway --internet-gateway-id "$internetGatewayId" --vpc-id "$pubVPCID"
aws ec2 create-tags --resources $internetGatewayId --tags 'Key=Name,Value=pubVPC-Internet-Gateway'
```

### Create the subnets
Lets create two subnets each in different availability zones within the same region. This allows us to test the NFS mount across availability zones.
```sh
### Create the subnets for to spread the instances across multiple AZs
pubVPC_Subnet01ID=$(aws ec2 create-subnet --vpc-id \
                    "$pubVPCID" \
                    --cidr-block 10.0.1.0/25 \
                    --availability-zone us-west-1a \
                    --query 'Subnet.SubnetId' \
                    --output text)

pubVPC_Subnet02ID=$(aws ec2 create-subnet \
                    --vpc-id "$pubVPCID" \
                    --cidr-block 10.0.1.128/25 \
                    --availability-zone us-west-1c \
                    --query 'Subnet.SubnetId' \
                    --output text)

#### Tag the subnet ID's
aws ec2 create-tags --resources "$pubVPC_Subnet01ID" --tags 'Key=Name,Value=pubVPC_Subnet01-west-1a'
aws ec2 create-tags --resources "$pubVPC_Subnet02ID" --tags 'Key=Name,Value=pubVPC_Subnet02-west-1c'
```

#### Add the Routes
```sh
### Create public routes and associate with internet gateway
routeTableID=$(aws ec2 create-route-table --vpc-id "$pubVPCID" --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id "$routeTableID" \
                     --destination-cidr-block 0.0.0.0/0 \
                     --gateway-id "$internetGatewayId"
                     
aws ec2 associate-route-table --route-table-id "$routeTableID" --subnet-id "$pubVPC_Subnet01ID"
aws ec2 associate-route-table --route-table-id "$routeTableID" --subnet-id "$pubVPC_Subnet02ID"
```
### Create two security groups
Both an Amazon EC2 instance and a mount target need to have associated security groups. These security groups act as a virtual firewall that controls the traffic between them. You can use the security group you associated with the mount target to control inbound traffic to your file system by adding an inbound rule to the mount target security group that allows access from a specific EC2 instance. Then, you can mount the file system only on that EC2 instance.

```sh
### Creating a security group for the public instances
efsSecGrpID=$(aws ec2 create-security-group --group-name efsSecGrp \
              --description "Security Group for public instances" \
              --vpc-id "$pubVPCID" \
              --output text)

ec2SecGrpID=$(aws ec2 create-security-group --group-name ec2SecGrp \
              --description "Security Group for public instances" \
              --vpc-id "$pubVPCID" \
              --output text)

#### Tag the Security Group ID's
aws ec2 create-tags --resources "$efsSecGrpID" --tags 'Key=Name,Value=EFS-Security-Group'
aws ec2 create-tags --resources "$ec2SecGrpID" --tags 'Key=Name,Value=EC2-Security-Group'
```

#### Add Rules to the Security Groups to Authorize Inbound/Outbound Access
```sh
#### Add a rule that allows inbound SSH ( from any source ) to our EC2 Instances
aws ec2 authorize-security-group-ingress \
        --group-id "$ec2SecGrpID" \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0
#### Add a rule that allows inbound to our mount only from our EC2 Instances
aws ec2 authorize-security-group-ingress \
        --group-id "$efsSecGrpID" \
        --protocol tcp \
        --port 2049 \
        --source-group "$ec2SecGrpID" 
```

## Create EC2 Instance
```sh
##### EC2 Instances
nfsClientInstID=$(aws ec2 run-instances \
                  --image-id ami-d1315fb1 \
                  --count 1 \
                  --instance-type t2.micro \
                  --key-name efsec2-key \
                  --security-group-ids "$ec2SecGrpID" \
                  --subnet-id "$pubVPC_Subnet01ID" \
                  --associate-public-ip-address \
                  --query 'Instances[0].InstanceId' \
                  --output text)

aws ec2 create-tags --resources "$nfsClientInstID" --tags 'Key=Name,Value=NFS-Client-Instance'
```

## Create Amazon EFS File System
```sh

```