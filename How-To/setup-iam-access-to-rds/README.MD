# IAM Database Authentication for MySQL
Amazon RDS for MySQL you can authenticate using AWS Identity and Access Management (IAM) database authentication. With this authentication method, you don't need to use a password when you connect to a DB instance. Instead, you use an authentication token.

An `authentication token` is a unique string of characters that Amazon RDS generates on request. Authentication tokens are generated using AWS Signature Version 4. Each token has a lifetime of 15 minutes. You don't need to store user credentials in the database, because authentication is managed externally using IAM. _You can also still use standard database authentication._

![IAM-Access-To-RDS](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-iam-access-to-rds/images/iam-access-to-rds-00.png)

Follow this article in **[Youtube](https://youtu.be/tvXZWhu35PY)**

## Pre-Requisites
1. EC2 Instance
   - AWS CLI Installed - [Get help here](https://www.youtube.com/watch?v=5g0Cuq-qKA0&list=PLxzKY3wu0_FLaF9Xzpyd9p4zRCikkD9lE&index=11)
1. MySQL RDS Instance - [Get help here](https://youtu.be/vLaW6b441x0)
   - MySQL Version - 5.7.17
   - Ensure `IAM DB authentication` is enabled
   - EC2 and RDS should be able to communicate with each other at port RDS port( For MySQL 3306 )
1. IAM RoleName: **ec2-to-rds**: An EC2 Role. [Get help here](https://www.youtube.com/watch?v=5g0Cuq-qKA0&index=11&list=PLxzKY3wu0_FLaF9Xzpyd9p4zRCikkD9lE)
   - Permissions: Managed Policies `AmazonRDSFullAccess`

## Prepare EC2 Instance
Install the following packages and commands
```sh
yum install curl mysql -y
service mysqld start
chkconfig mysqld on
```

### Setup Database to use IAM
We will now create a database user account that uses an AWS authentication token
```sh
# Connect to DB
RDS_HOST="db-with-iam-support.ct5b4uz1gops.eu-central-1.rds.amazonaws.com"
REGION="eu-central-1"
# mysql -h {database or cluster endpoint} -P {port number database is listening on} -u {master db username} -p
mysql -h ${RDS_HOST} -P 3306 -u dbuser -p
```

Run this command to create a database user account that will use an AWS authentication token instead of a password:
```sh
CREATE USER 'db_iam_user' IDENTIFIED WITH AWSAuthenticationPlugin as 'RDS';
```
Optionally, run this command to require the user to connect to the database using SSL: [Learn more here](https://github.com/miztiik/AWS-Demos/tree/master/How-To/setup-ssl-connection-to-rds)
```sh
GRANT USAGE ON *.* TO 'db_iam_user'@'%'REQUIRE SSL;
```

Run the “exit” command to close MySQL


### IAM Inline Policy
Inline Policy to allow the db access to user, _Change the db arn accordingly_
```sh
{
    "Version": "2012-10-17",
    "Statement": [
       {
          "Effect": "Allow",
          "Action": [
              "rds-db:connect"
          ],
          "Resource": [
              "arn:aws:rds-db:eu-central-1:111111111111:dbuser:db-RWXD2T7YIWZU4VI2FBHSM2GE24/db_iam_user"
          ]
       }
    ]
}
```

#### Download SSL Certificates
Download the AWS RDS Certificate `pem` file,
```sh
mkdir -p /var/mysql-certs/
cd /var/mysql-certs/
curl -O https://s3.amazonaws.com/rds-downloads/rds-combined-ca-bundle.pem
```

### Generate an AWS authentication token
The authentication token consists of several hundred characters. It can be unwieldy on the command line. One way to work around this is to save the token to an environment variable, and then use that variable when you connect.
```sh
TOKEN="$(aws rds generate-db-auth-token --hostname ${RDS_HOST} --port 3306 --region ${REGION} --username db_iam_user)"
```



## Connect to Database
```sh
mysql --host="${RDS_HOST}" \
      --port=3306 \
      --user=db_iam_user \
      --ssl-ca=/var/mysql-certs/rds-combined-ca-bundle.pem \
      --ssl-verify-server-cert \
      --enable-cleartext-plugin \
      --password="$TOKEN"
```


### Screenshots
![IAM-Access-To-RDS](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-iam-access-to-rds/images/iam-access-to-rds-01.png)


##### References
[1] - [AWS Docs - IAM Policy for IAM Database Access](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.IAMDBAuth.IAMPolicy.html)

[2] - [AWS Docs - Amazon RDS with IAM credentials](https://aws.amazon.com/premiumsupport/knowledge-center/users-connect-rds-iam/)
