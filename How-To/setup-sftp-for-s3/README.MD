# SFTP Service for Amazon S3

AWS Transfer for SFTP is a fully-managed, highly-available SFTP service. 

Follow this article in **[Youtube](https://youtu.be/Ysd9tWuhE8g)**

![SFTP Service for Amazon S3](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-sftp-for-s3/images/sftp-for-s3-valaxy-miztiik.png)

### Prerequisites
1. S3 Bucket - BucketName (_For ex:: `sftp.dest.testbkt`)_
   - _You will have to create your own bucket and use that name in the instructions_
1. SFTP Client 
   - Preferably a linux machine as sftp client is available by default.
   - If you are using Windows, then you can use _WinSCP_
1. IAM Role for SFTP Users
   - Trust Relationship


## Create the SFTP Server
You can basically have have your custom endpoint with your domain name or can use the default endpoint


### Setup IAM Role for Users
Create a IAM Role with `AmazonS3FullAccess` (_You can restrict this to particular bucket/user_) with the following trust relationships.
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "transfer.amazonaws.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {}
    }
  ]
}
```

#### Set up users
You will need a SSH Key pair, and upload the public key that the user will use when connecting to the SFTP server,

#### Create SSH Keypair
From linux server you can do this, (you can do the same in windows using putty-gen)
```sh
>ssh-keygen -P "" -f "sftp-test-key"
```



#### Connect to SFTP Server
```sh
>sftp -i sftp-test-key testuser@YOUR-SFTP-END-POINT

# To list files
>ls

# To upload files
>mput YOUR-FILE-NAME

>ls
```
