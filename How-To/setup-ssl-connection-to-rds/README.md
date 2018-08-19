# Security in Amazon RDS - Using SSL to Encrypt Connection to DB

It is good practice to use SSL to encrypt a connection from your application to a DB instance running MySQL, MariaDB, Amazon Aurora, SQL Server, Oracle, or PostgreSQL. Each DB engine has its own process for implementing SSL.

![](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-ssl-connection-to-rds/images/SSL-to-RDS.png)

Follow this article in **[Youtube](https://www.youtube.com/channel/UC_evcfxhjjui5hChhLE08tQ/playlists)**

## Securing MySQL: Using SSL with a MySQL DB Instance
Amazon RDS creates an SSL certificate and installs the certificate on the DB instance when Amazon RDS provisions the instance. These certificates are signed by a certificate authority. The SSL certificate includes the DB instance endpoint as the Common Name (CN) for the SSL certificate to guard against spoofing attacks. The public key is stored at `https://s3.amazonaws.com/rds-downloads/rds-combined-ca-bundle.pem`.

#### Prerequisites
 - An AWS RDS Instance running MySQL DB - [Click here to set it up](https://youtu.be/iwTHRT9p6fI?t=30)
 - An `mysql` client - An [EC2 instance](https://youtu.be/N_mP4mIqK8A) with `mysql` pre-installed

##### Optional
Try to connect to the db, and check if ssl is enforced,
```sh
mysql> \s
--------------
...
SSL:                    Not in use
```

### Enable SSL Only Connection to User
You can require SSL connections for specific users accounts. For example, you can use the following statements to require SSL connections on the user account `encrypted_user`.

```sh
ALTER USER 'encrypted_user'@'%' REQUIRE SSL; 
```

### Connect to DB with SSL
Download the AWS RDS Certificate `pem` file,
```sh
mkdir -p /var/mysql-certs/
cd /var/mysql-certs/
curl -O https://s3.amazonaws.com/rds-downloads/rds-combined-ca-bundle.pem
```
Connect to db using the certificates,
```sh
mysql -h only-ssl-db.ct5b4uz1gops.eu-central-1.rds.amazonaws.com --ssl-ca=/var/mysql-certs/rds-combined-ca-bundle.pem --ssl-mode=REQUIRED -u onlyssldbusr -P 3306 -p
```

To determine whether the current connection with the server uses encryption, check the value of the Ssl_cipher status variable. If the value is empty, the connection is not encrypted. Otherwise, the connection is encrypted and the value indicates the encryption cipher. For example:


### Validate SSL Connection
```sh
mysql> SHOW SESSION STATUS LIKE 'Ssl_cipher';
+---------------+--------------------+
| Variable_name | Value              |
+---------------+--------------------+
| Ssl_cipher    | DHE-RSA-AES256-SHA |
+---------------+--------------------+

or
mysql> \s
...
SSL: Cipher in use is DHE-RSA-AES256-SHA


or
mysql> show status like 'Ssl%';
+--------------------------------+---------------------------------------------------------------------------------------------------+
| Variable_name                  | Value                                                                                             |
+--------------------------------+---------------------------------------------------------------------------------------------------+
|...                             | ...                                                                                               |
| Ssl_cipher                     | DHE-RSA-AES256-SHA                                                                                |
| Ssl_cipher_list                | AES256-SHA:AES128-SHA:DHE-RSA-AES256-SHA:DHE-DSS-AES256-SHA:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA |
|...                             | ...                                                                                               |
| Ssl_version                    | TLSv1                                                                                             |
+--------------------------------+---------------------------------------------------------------------------------------------------+


```

## Securing MSSQL: Using SSL with a MSSQL DB Instance
When you create a SQL Server DB instance, Amazon RDS creates an SSL certificate for it. The SSL certificate includes the DB instance endpoint as the Common Name (CN) for the SSL certificate to guard against spoofing attacks. If you force connections to use SSL, it happens transparently to the client, and the **client doesn't have to do any work to use SSL**.

 Out of the two ways to secure MSSQL, We will use `Force SSL for all connections`.

### Forcing Connections to Your DB Instance to Use SSL
If you want to force SSL, use the `rds.force_ssl` parameter. By default, the `rds.force_ssl` parameter is set to `false`. Set the `rds.force_ssl` parameter to `true` to force connections to use SSL.

1. Create Custom Parameter Group for your DB
1. Update the `rds.force_ssl` to `true`
1. Start your DB instance with the _custom parameter group_
1. Check connection from your client.


###### Creating Users in MySQL
```sh
CREATE USER 'USER_NAME'@'%' IDENTIFIED BY 'PASSWORD';
GRANT ALL PRIVILEGES ON YOUR_DATABASE_NAME_HERE.* TO 'USER_NAME'@'%' WITH GRANT OPTION;
FLUSH PRIVILEGES;

ALTER USER 'USER_NAME'@'%' REQUIRE SSL;
FLUSH PRIVILEGES;
```

##### References
[1] - [AWS Docs - Using SSL to Encrypt a Connection to a DB Instance](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.SSL.html)