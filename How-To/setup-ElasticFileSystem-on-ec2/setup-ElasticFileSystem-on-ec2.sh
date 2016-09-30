#!/bin/bash
set -x -e

# Setting the Region & Availability Zone
prefRegion=us-west-2
prefRegionAZ1=us-west-2a
prefRegionAZ2=us-west-2c
amiID=ami-775e4f16

export AWS_DEFAULT_REGION="$prefRegion"

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

### Create the subnets for to spread the instances across multiple AZs
pubVPC_Subnet01ID=$(aws ec2 create-subnet --vpc-id \
                    "$pubVPCID" \
                    --cidr-block 10.0.1.0/25 \
                    --availability-zone "$prefRegionAZ1" \
                    --query 'Subnet.SubnetId' \
                    --output text)

pubVPC_Subnet02ID=$(aws ec2 create-subnet \
                    --vpc-id "$pubVPCID" \
                    --cidr-block 10.0.1.128/25 \
                    --availability-zone "$prefRegionAZ2" \
                    --query 'Subnet.SubnetId' \
                    --output text)

#### Tag the subnet ID's
aws ec2 create-tags --resources "$pubVPC_Subnet01ID" --tags Key=Name,Value=pubVPC_Subnet01-"$prefRegionAZ1"
aws ec2 create-tags --resources "$pubVPC_Subnet02ID" --tags Key=Name,Value=pubVPC_Subnet01-"$prefRegionAZ2"

### Create public routes and associate with internet gateway
routeTableID=$(aws ec2 create-route-table --vpc-id "$pubVPCID" --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id "$routeTableID" \
                     --destination-cidr-block 0.0.0.0/0 \
                     --gateway-id "$internetGatewayId"
rtassn01=$(aws ec2 associate-route-table --route-table-id "$routeTableID" --subnet-id "$pubVPC_Subnet01ID")
rtassn02=$(aws ec2 associate-route-table --route-table-id "$routeTableID" --subnet-id "$pubVPC_Subnet02ID")

### Creating a security group for the public instances
efsSecGrpID=$(aws ec2 create-security-group --group-name efsSecGrp \
              --description "Security Group for public instances" \
              --vpc-id "$pubVPCID" \
              --output text)

ec2SecGrpID=$(aws ec2 create-security-group --group-name ec2SecGrp \
              --description "Security Group for public instances" \
              --vpc-id "$pubVPCID" \
              --output text)

#### Tag the subnet ID's
aws ec2 create-tags --resources "$efsSecGrpID" --tags 'Key=Name,Value=EFS-Security-Group'
aws ec2 create-tags --resources "$ec2SecGrpID" --tags 'Key=Name,Value=EC2-Security-Group'

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

## Create Amazon EFS File System
efsID=$(aws efs create-file-system --creation-token "efs-demo" --query 'FileSystemId' --output text)
##### Tag the EFS Filesystem
aws efs create-tags --file-system-id "$efsID" --tags 'Key=Name,Value=EFS-Demo-FileSystem'

### Create a Mount Target
efsMountTargetID=$(aws efs create-mount-target \
        --file-system-id "$efsID" \
        --subnet-id  "$pubVPC_Subnet01ID" \
        --security-group "$efsSecGrpID" \
        --query 'MountTargetId' \
        --output text)

### Mount the Amazon EFS File System on the EC2 Instance and Test

efsDNS="$prefRegionAZ1"."$efsID".efs."$prefRegion".amazonaws.com


### Create two EC2 Instances

##### EC2 Instances

cat >> userDataScript <<EOF
#!/bin/bash
set -e -x
yum -y install nfs-utils
mkdir -p /var/efs-mount-point
mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 "$efsDNS":/ /var/efs-mount-point
cd /var/efs-mount-point
EOF


nfsClientInst01ID=$(aws ec2 run-instances \
                  --image-id "$amiID" \
                  --count 1 \
                  --instance-type t2.micro \
                  --key-name efsec2-key \
                  --security-group-ids "$ec2SecGrpID" \
                  --subnet-id "$pubVPC_Subnet01ID" \
                  --user-data file://userDataScript \
                  --associate-public-ip-address \
                  --query 'Instances[0].InstanceId' \
                  --output text)                 

nfsClientInst01Url=$(aws ec2 describe-instances \
                 --instance-ids "$nfsClientInst01ID" \
                 --query 'Reservations[0].Instances[0].PublicDnsName' \
                 --output text)

nfsClientInst02ID=$(aws ec2 run-instances \
                  --image-id "$amiID" \
                  --count 1 \
                  --instance-type t2.micro \
                  --key-name efsec2-key \
                  --security-group-ids "$ec2SecGrpID" \
                  --subnet-id "$pubVPC_Subnet02ID" \
                  --user-data file://userDataScript \
                  --associate-public-ip-address \
                  --query 'Instances[0].InstanceId' \
                  --output text)                 

nfsClientInst02Url=$(aws ec2 describe-instances \
                 --instance-ids "$nfsClientInst02ID" \
                 --query 'Reservations[0].Instances[0].PublicDnsName' \
                 --output text)                 

##### Tag the instances
aws ec2 create-tags --resources "$nfsClientInst01ID" --tags 'Key=Name,Value=NFS-Client-Instance-01'
aws ec2 create-tags --resources "$nfsClientInst02ID" --tags 'Key=Name,Value=NFS-Client-Instance-02'


## Login to the instance to create files
cd /usr/efs-mount-point
touch this-is-awesome
# To create big files for testing
# dd if=/dev/urandom of=sample-bigFile.txt bs=64M count=2


################################################ 
############ DELETING THE RESOURCES ############
################################################


## Terminate the EC2 Instanes
# aws ec2 terminate-instances --instance-ids "$nfsClientInst01ID" "$nfsClientInst02ID"

## Delete the Mount Targets
# aws efs delete-mount-target --mount-target-id "$efsMountTargetID"

## Delete the EFS
# aws efs delete-file-system --file-system-id "$efsID"

## Delete the Security groups
# aws ec2 delete-security-group --group-id "$efsSecGrpID"
# aws ec2 delete-security-group --group-id "$ec2SecGrpID"

## Disassociate route table
# aws ec2 disassociate-route-table --association-id "$rtassn01"
# aws ec2 disassociate-route-table --association-id "$rtassn02"

## Delete the route 
# aws ec2 delete-route --route-table-id "$routeTableID" --destination-cidr-block 0.0.0.0/0

## Delete route table
# aws ec2 delete-route-table --route-table-id "$routeTableID"

## Detach & Delete Internet Gateway
# aws ec2 detach-internet-gateway --internet-gateway-id "$internetGatewayId" --vpc-id "$pubVPCID"
# aws ec2 delete-internet-gateway --internet-gateway-id "$internetGatewayId"

## Delete Subnets
# aws ec2 delete-subnet --subnet-id "$pubVPC_Subnet01ID"
# aws ec2 delete-subnet --subnet-id "$pubVPC_Subnet02ID"

## Delete the VPC
# aws ec2 delete-vpc --vpc-id "$pubVPCID"