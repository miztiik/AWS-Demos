# CloudFormation Template to setup Wordpress

This templates is written in `YAML` format to assist in easier comprehension, feel free to rewrite it in `JSON`

The following resources are setup in this template,
- Parameters
  - VPC CIDR Range
  - Availability Zone Choices
  - Subnet CIDR Choices
  - Instance Name
  - Instance Type - Forced to `t2.micro`
  - KeyName (Picked up from account)

- Mappings
  - Regions - Mapped to `us-east-1` and `ap-south-1`
- Resources
  - VPC
  - Internet Gateway
  - Routes and Routing Table for internet traffic
  - Two subnets [ Public & Private ]
  - Security Group to allow internet traffic
  - Webserver running wordpress with local `MySQL` database

### Access Wordpress
Open the public url of the ec2 instance in your browser to access the wordpress site
  
