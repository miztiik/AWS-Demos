# Create Amazon EFS File System and Mount it on EC2 Instance(s)

## Why you need EFS File System?
Suppose you have one or more EC2 instances launched in your VPC. Now you want to create and share a file system on these instances, EFS is your friend. You can mount an Amazon EFS file system on EC2 instances in your Amazon Virtual Private Cloud (Amazon VPC) using the Network File System version 4.1 protocol (NFSv4.1). Amazon EFS provides elastic, shared file storage that is
 - **POSIX-compliant**
 - Supports **concurrent read and write access** from multiple Amazon EC2 instances
 - Accessible from all of the `Availability Zones` in the `AWS Region`

Having said that, Beware of some of the _[not supported features of EFS](http://docs.aws.amazon.com/efs/latest/ug/nfs4-unsupported-features.html)_ & [limitations](http://docs.aws.amazon.com/efs/latest/ug/limits.html), For example Elastic File System is [not available](http://docs.aws.amazon.com/general/latest/gr/rande.html#elasticfilesystem_region) in all regions.


In this walkthrough, you will create the following resources:
 - Amazon EC2 resources,
   - Two security groups (for your EC2 instance and Amazon EFS file system) - You add rules to these security groups to authorize appropriate inbound/outbound access to allow your EC2 instance to connect to the file system via the mount target using a standard NFSv4.1 TCP port.
   - An Amazon EC2 instance in your VPC.
 - Amazon EFS resources,
   - A file system.
   - A mount target for your file system - To mount your file system on an EC2 instance you need to create a mount target in your VPC. You can create one mount target in each of the Availability Zones in your VPC. 
![Fig 1 : EFS on EC2 Architecture Context](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/img/Elastic-FileSystem-EC2.jpg)

## Creating EC2 Resources

### Create the VPC
Lets create a /24 VPC and tag it `pubVPC` along with the interget gateway

```sh
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
```

### Create the subnets
Lets create two subnets each in different availability zones within the same region. This allows us to test the NFS mount across availability zones.
```sh
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
aws ec2 create-tags --resources "$pubVPC_Subnet01ID" --tags 'Key=Name,Value=pubVPC_Subnet01-west-2a'
aws ec2 create-tags --resources "$pubVPC_Subnet02ID" --tags 'Key=Name,Value=pubVPC_Subnet02-west-2c'
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

Add a rule that allows inbound SSH ( from any source ) to our EC2 Instances
```sh
aws ec2 authorize-security-group-ingress \
        --group-id "$ec2SecGrpID" \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0
```
 Add a rule that allows inbound to the EFS Security group to allow traffic only from our EC2 Instances
```sh
aws ec2 authorize-security-group-ingress \
        --group-id "$efsSecGrpID" \
        --protocol tcp \
        --port 2049 \
        --source-group "$ec2SecGrpID" 
```

## Create Amazon EFS File System
```sh
## Create Amazon EFS File System
efsID=$(aws efs create-file-system --creation-token "efs-demo" --query 'FileSystemId' --output text)

##### Tag the EFS Filesystem
aws efs create-tags --file-system-id "$efsID" --tags 'Key=Name,Value=EFS-Demo-FileSystem'
```
### Create a Mount Target
Create a mount target for your file system in the Availability Zone where you have your EC2 instance launched, In our case it will be `us-west-2a`
```sh
### Create a Mount Target
efsMountTargetID=$(aws efs create-mount-target \
        --file-system-id "$efsID" \
        --subnet-id  "$pubVPC_Subnet01ID" \
        --security-group "$efsSecGrpID" \
        --query 'MountTargetId' \
        --output text)
```
You can also use the `describe-mount-targets` command to get descriptions of mount targets you created on a file system.
```sh
~]# aws efs describe-mount-targets --file-system-id "$efsID" --region "$prefRegion"
{
    "MountTargets": [
        {
            "MountTargetId": "fsmt-d31de57a",
            "NetworkInterfaceId": "eni-ce264ab1",
            "FileSystemId": "fs-1fb049b6",
            "LifeCycleState": "available",
            "SubnetId": "subnet-77edd613",
            "OwnerId": "xxxxxxxxxxxx",
            "IpAddress": "10.0.1.57"
        }
    ]
}
```

### Launch EC2 Instances
Gather the following information before you create the instance. But do note that, _Amazon EFS does not require that your Amazon EC2 instance have either a public IP address or public DNS name_.
  - Security Group ID of the security group you created for an EC2 instance, i.e., `ec2SecGrpID`
  - Subnet ID – You need this value when you create a mount target. In this exercise, you create a mount target in the same subnet where you launch an EC2 instance. In our demo are we going to use `pubVPC_Subnet01ID`
  - Availability Zone of the subnet – You need this to construct your mount target DNS name, which you use to mount a file system on the EC2 instance. i.e., `prefRegionAZ1`
  - Key Pair Name
  - AMI ID - Which supports NFS - `amiID`

##### Mount the Amazon EFS File System on the EC2 Instance
We need the DNS name of your file system's mount target to be used in our `user-data` script. You can construct this DNS name using the following generic form: 
    `availability-zone`.`file-system-id`.efs.`aws-region`.amazonaws.com

  ```sh
  efsDNS="$prefRegionAZ1"."$efsID".efs."$prefRegion".amazonaws.com
  ```
We will be creating two instanes each in different availability zone. Since the `user-data` script attempts to mount the NFS, this step will have to be done after the EFS creation.

```sh
## User data script to install the NFS client and mount the NFS Directory
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
```

## Testing the NFS Mount
Login into one of the EC2 Instance and create a file
```sh
[ec2-user@nfsclient01 efs-mount-point]$ df -h /usr/efs-mount-point/
Filesystem                                            Size  Used Avail Use% Mounted on
us-west-2a.fs-1fb049b6.efs.us-west-2.amazonaws.com:/  8.0E     0  8.0E   0% /usr/efs-mount-point
[ec2-user@nfsclient01 efs-mount-point]$ cd /usr/efs-mount-point/
[ec2-user@nfsclient01 efs-mount-point]$ touch this-is-awesome
[ec2-user@nfsclient01 efs-mount-point]$ ls -la .
total 12
drwxrwxrwx.  2 root     root     4096 Sep 30 17:25 .
drwxr-xr-x. 14 root     root     4096 Sep 30 17:24 ..
-rw-rw-r--.  1 ec2-user ec2-user    0 Sep 30 17:25 this-is-awesome
[ec2-user@nfsclient01 efs-mount-point]$
```

Login to the second EC2 Insance and check out the EFS for the file `this-is-awesome`
```sh
[ec2-user@nfsclient02 efs-mount-point]$ ls -la .
total 12
drwxrwxrwx.  2 root     root     4096 Sep 30 17:25 .
drwxr-xr-x. 14 root     root     4096 Sep 30 17:20 ..
-rw-rw-r--.  1 ec2-user ec2-user    0 Sep 30 17:25 this-is-awesome
[ec2-user@nfsclient02 efs-mount-point]$
```

### Testing with big file
Lets create a random big file of some 128MB using `dd` in `nfsclient02`
```sh
[ec2-user@nfsclient01 efs-mount-point]$ dd if=/dev/urandom of=sample-bigFile.txt bs=64M count=2
2+0 records in
2+0 records out
134217728 bytes (134 MB) copied, 12.2977 s, 10.9 MB/s
[ec2-user@nfsclient01 efs-mount-point]$ ls -lart .
total 131084
drwxr-xr-x. 14 root     root          4096 Sep 30 17:24 ..
-rw-rw-r--.  1 ec2-user ec2-user         0 Sep 30 17:25 this-is-awesome
drwxrwxrwx.  2 root     root          4096 Sep 30 17:34 .
-rw-rw-r--.  1 ec2-user ec2-user 134217728 Sep 30 17:36 sample-bigFile.txt
[ec2-user@nfsclient01 efs-mount-point]$ du -h /usr/efs-mount-point
129M    /usr/efs-mount-point
```
From `nfsclient02`,
```sh
[ec2-user@nfsclient02 efs-mount-point]$ du -h /usr/efs-mount-point/
129M    /usr/efs-mount-point/
[ec2-user@nfsclient02 efs-mount-point]$ ls -lart .
total 131084
drwxr-xr-x. 14 root     root          4096 Sep 30 17:20 ..
-rw-rw-r--.  1 ec2-user ec2-user         0 Sep 30 17:25 this-is-awesome
drwxrwxrwx.  2 root     root          4096 Sep 30 17:34 .
-rw-rw-r--.  1 ec2-user ec2-user 134217728 Sep 30 17:36 sample-bigFile.txt
```
###### The file system you mounted will not persist across reboots. To automatically remount the directory you can use the fstab file.

It should of the below format
```sh
mount-target-DNS:/ efs-mount-point nfs4 nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 0 0
```