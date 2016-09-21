# Creating & Installing Self Signed Certificates

_This article is aimed for people looking to create and use self signed certificates for learning & testing purposes_



 We will work our way through the following actions
 - Setup Webserver - An EC2 Instance with internet access, Ports 80 & 443 open
   - Ensure `mod_ssl` is installed in the webserver
 - Generate the encryptions keys and certificate using `OpenSSL`
 - Install the SSL certificate in webserver.

 **Assumptions**,
  - Access to linux instance (our Client) - We will be using this instance to generate the certs
  - AWS EC2 Linux - RedHAT - our WebServer
  - Thats it.


## Setup the Webserver

The following EC2 Instance attributes are to be pre-determined before executing the script
  - `userdata` Script to setup our webserver as an EC2 Instance running Apache HTTP server on Redhat Linux
    - `mod_ssl` package is needed for using SSL Certificates in your webserver.  `mod_ssl` installation will create the required configuration file `/etc/httd/conf.d/ssl.conf`. For this file to be loaded, and hence for mod_ssl to work, you must have the statement `Include conf.d/*.conf` in the `/etc/httpd/conf/httpd.conf` file.
    - >_This statement is included by default in the default Apache HTTP Server configuration file._
  - `ami-cdbdd7a2` is the latest ami for Redhat Linux in Region:`ap-south-1`
  - Ensure you have the internet gateway and security group setup & Network ACL set properly for allowing TCP traffic through port `SSH - 22, HTTP - 80 & HTTPS - 443`


```sh
# Setting the Region
prefAZ=ap-south-1
export AWS_DEFAULT_REGION="$prefAZ"

# Setup the command to run at boot time
cat > userDataScript << "EOF"
#!/bin/bash
yum install -y httpd mod_ssl openssl
service httpd start
chkconfig httpd on
groupadd www
usermod -a -G www ec2-user
chown -R root:www /var/www
chmod 2775 /var/www
find /var/www -type d -exec chmod 2775 {} +
find /var/www -type f -exec chmod 0664 {} +
echo "Lets rock the HTTPS World; Just give me a lever long enough" > /var/www/html/index.html
EOF
```

```sh
instanceID=$(aws ec2 run-instances \
           --image-id ami-cdbdd7a2 \
           --count 1 \
           --instance-type t2.micro \
           --key-name lms-key \
           --user-data "$userDataScript" \
           --associate-public-ip-address \
           --query 'Instances[0].InstanceId' \
           --output text)

instanceUrl=$(aws ec2 describe-instances \
            --instance-ids "$instanceID" \
            --query 'Reservations[0].Instances[0].PublicDnsName' \
            --output text)
```

## Generate the private key

We will be using Apache to generate our "Generate Your Apache "Self Signed Certificate", If If `openssl` is not installed, run `yum install -y openssl`. This key is a 2048 bit RSA key and stored in a PEM format so that it is readable as ASCII text.

```sh
openssl genrsa -out mystique.key 2048
```
_Output_
```
[root@ip-10-0-5-105 tmp]# openssl genrsa -out mystique.key 2048
Generating RSA private key, 2048 bit long modulus
...+++
.............................................................+++
e is 65537 (0x10001)
[root@ip-10-0-5-105 tmp]# ls -l mystique.key
-rw-r--r--. 1 root root 1679 Sep 20 14:14 mystique.key
[root@ip-10-0-5-105 tmp]#
```

## Generate the Self-Signed Certificate
Your certificate will use the `key` created in the previous step
```sh
openssl req -days 365 -new -key mystique.key -x509 -out mystique.crt
```

You will be prompted for,
  - `Organizational information and a common name` : The common name should be the fully qualified domain name for the site you are securing.
  - `E-Mail address`
  - `Challenge password`
  - `Company name`

```
[root@ip-10-0-5-105 tmp]# openssl req -days 365 -new -key mystique.key -x509 -out mystique.crt
You are about to be asked to enter information that will be incorporated
into your certificate request.
What you are about to enter is what is called a Distinguished Name or a DN.
There are quite a few fields but you can leave some blank
For some fields there will be a default value,
If you enter '.', the field will be left blank.
-----
Country Name (2 letter code) [XX]:IN
State or Province Name (full name) []:someSTATE
Locality Name (eg, city) [Default City]:someCITY
Organization Name (eg, company) [Default Company Ltd]:Mystique Corp
Organizational Unit Name (eg, section) []:IT
Common Name (eg, your name or your server's hostname) []:ip-10-0-5-105.ap-south-1.compute.internal
Email Address []:none@none.com
[root@ip-10-0-5-105 tmp]#
```
 
 When the command is finished running, it will create two files: a mystique.key file and a mystique.crt self signed certificate file valid for 365 days.

```sh
[root@ip-10-0-5-105 tmp]# ls -l mystique*
-rw-r--r--. 1 root root 1505 Sep 20 14:24 mystique.crt
-rw-r--r--. 1 root root 1679 Sep 20 14:14 mystique.key
```

### Move your certificate file to 
`mv mystique.crt /etc/pki/tls/certs/mystique.crt`
### Move your Key file to:
 `mv mystique.key /etc/pki/tls/private/mystique.key`

### Configure Apache to user our certificates
Find the below entries in the file `/etc/httd/conf.d/ssl.conf`, and update them as shown below
```sh
SSLCertificateFile /etc/httpd/conf/ssl.crt/server.crt
SSLCertificateKeyFile /etc/httpd/conf/ssl.key/server.key
```

## Restart Webserver
Now we have generated the certificates and installed them in ou
```sh
systemctl restart httpd
```

## Testing SSL Protocols
###### You should _really_ check it from a browser
![alt tag](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/img/home-made-ssl.png)
Incase you want to play around in the commandline, To check which versions of SSL are enabled or disabled, make use of the following command. 
`openssl s_client -connect hostname:port -protocol`
```sh
openssl s_client -connect hostname:port -protocol

~]$ openssl s_client -connect localhost:443 -tls1_2
CONNECTED(00000003)
depth=0 C = --, ST = SomeState, L = SomeCity, O = SomeOrganization, OU = SomeOrganizationalUnit, CN = localhost.localdomain, emailAddress = root@localhost.localdomain
output omitted
New, TLSv1/SSLv3, Cipher is ECDHE-RSA-AES256-GCM-SHA384
Server public key is 2048 bit
Secure Renegotiation IS supported
Compression: NONE
Expansion: NONE
SSL-Session:
    Protocol  : TLSv1.2
output truncated
```
_The above output indicates that no failure of the handshake occurred and a set of ciphers was negotiated._

#### curl the localhost
```sh
[root@ip-10-0-5-105 tmp]# curl localhost:443
<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>400 Bad Request</title>
</head><body>
<h1>Bad Request</h1>
<p>Your browser sent a request that this server could not understand.<br />
Reason: You're speaking plain HTTP to an SSL-enabled server port.<br />
 Instead use the HTTPS scheme to access this URL, please.<br />
</p>
</body></html>
```
#### curl the hostname
```sh
[root@ip-10-0-5-105 tmp]# hostname
ip-10-0-5-105.ap-south-1.compute.internal
[root@ip-10-0-5-105 tmp]# curl ip-10-0-5-105.ap-south-1.compute.internal:443
<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>400 Bad Request</title>
</head><body>
<h1>Bad Request</h1>
<p>Your browser sent a request that this server could not understand.<br />
Reason: You're speaking plain HTTP to an SSL-enabled server port.<br />
 Instead use the HTTPS scheme to access this URL, please.<br />
</p>
</body></html>
```

#### curl the public IP

```sh
[root@ip-10-0-5-105 tmp]# curl https://52.66.134.226/
curl: (60) Peer's certificate issuer has been marked as not trusted by the user.
More details here: http://curl.haxx.se/docs/sslcerts.html

curl performs SSL certificate verification by default, using a "bundle"
 of Certificate Authority (CA) public keys (CA certs). If the default
 bundle file isn't adequate, you can specify an alternate file
 using the --cacert option.
If this HTTPS server uses a certificate signed by a CA represented in
 the bundle, the certificate verification probably failed due to a
 problem with the certificate (it might be expired, or the name might
 not match the domain name in the URL).
If you'd like to turn off curl's verification of the certificate, use
 the -k (or --insecure) option.
[root@ip-10-0-5-105 tmp]#
```
