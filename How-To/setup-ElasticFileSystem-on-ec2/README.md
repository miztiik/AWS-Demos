# Create Amazon EFS File System and Mount It on an EC2 Instance

## Why you need EFS File System?
Suppose you have one or more EC2 instances launched in your VPC. Now you want to create and share a file system on these instances, EFS is your friend.

Amazon EFS provides elastic, shared file storage that is **POSIX-compliant**. The file system you create supports concurrent read and write access from multiple Amazon EC2 instances and is accessible from all of the `Availability Zones` in the `AWS Region` where it is created. Beware of some of the _[not supported features of EFS](http://docs.aws.amazon.com/efs/latest/ug/nfs4-unsupported-features.html)_

You can mount an Amazon EFS file system on EC2 instances in your Amazon Virtual Private Cloud (Amazon VPC) using the Network File System version 4.1 protocol (NFSv4.1).

In this walkthrough, you will create the following resources"
 - Amazon EC2 resources - 
   - Two security groups (for your EC2 instance and Amazon EFS file system) - You add rules to these security groups to authorize appropriate inbound/outbound access to allow your EC2 instance to connect to the file system via the mount target using a standard NFSv4.1 TCP port.
   - An Amazon EC2 instance in your VPC.
 - Amazon EFS resources:
   - A file system.
   - A mount target for your file system - To mount your file system on an EC2 instance you need to create a mount target in your VPC. You can create one mount target in each of the Availability Zones in your VPC. For more information, see Amazon EFS: How it Works.
## Cr
