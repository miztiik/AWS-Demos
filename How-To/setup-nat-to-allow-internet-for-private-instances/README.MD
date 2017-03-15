## Why do i need NAT Instances?
Sometimes you dont want to expose your instances to the public and put them behind another hardened instances. A network address translation (NAT) instance in a public subnet in your VPC enables instances in the private subnet to initiate outbound IPv4 traffic to the Internet or other AWS services, but prevent the instances from receiving inbound traffic initiated by someone on the Internet.

![Fig 1 : AWS-NAT-Instance-Miztiik-Demo](https://github.com/miztiik/AWS-Demos/blob/master/img/VPC-NAT-Instance.png)

## How does NAT Instances work?

The main route table sends the traffic from the instances in the private subnet to the NAT instance in the public subnet. The NAT instance sends the traffic to the Internet gateway for the VPC.
_**For Responses from remote system**_, The NAT instance specifies a high port number for the response; if a response comes back, the NAT instance sends it to an instance in the private subnet based on the port number for the response.



## Starting the NAT Instance
Amazon customized linux instaces which run as NAT instances. We can search for them in the community AMI for `amzn-ami-vpc-nat`

Pre-Requisities
 - VPC with two subnets ( Public & Private ) with internet gateway - [Refer here](https://github.com/miztiik/AWS-Demos/tree/master/How-To/setup-multi-az-vpc-from-scratch-using-boto) if you need help.
 - EC2 Parameters
  - EC2 Instance ID & Type
  - Keyname is ready

# Disabling Source/Destination Checks
Each EC2 instance performs source/destination checks by default. This means that the instance must be the source or destination of any traffic it sends or receives. However, a NAT instance must be able to send and receive traffic when the source or destination is not itself. Therefore, we **must** disable source/destination checks on the NAT instance.

