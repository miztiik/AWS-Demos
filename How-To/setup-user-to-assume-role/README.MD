# Assume IAM Role by an IAM User - Role to Delegate Permissions to an IAM User

A _role_ specifies a set of permissions that you can use to access AWS resources. To assume a role, an user calls the AWS STS `AssumeRole` API operation and passes the ARN of the role to use. The User/Application receive permissions to carry out required tasks and interact with AWS resources. The role can be in your own account or any other AWS account. This is useful when you need to give the temporary credentials to someone else. By default, your role session lasts for one hour.

**Important**:_The permissions of your IAM user and any roles that you assume are not cumulative. Only one set of permissions is active at a time. When you assume a role, you temporarily give up your previous user or role permissions and work with the permissions that are assigned to the role. When you exit the role, your user permissions are automatically restored._

Follow this article in **[Youtube](https://www.youtube.com/channel/UC_evcfxhjjui5hChhLE08tQ/playlists)**

![](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-pre-signed-s3-urls/images/signed-url-upload-flow.png)

### Prerequisite
1. IAM User - Name `Dave`: _Preferably with no permissions_
   1. EC2 with AWS CLI configured with above IAM User Credentials
1. IAM Role - `prod-dev-access-role` [Get help here](https://www.youtube.com/watch?v=5g0Cuq-qKA0&index=11&list=PLxzKY3wu0_FLaF9Xzpyd9p4zRCikkD9lE)
   - Attach managed permissions - `AmazonS3FullAccess`

### IAM User Policy Update
A user with a policy that allows them to call AssumeRole on the role you want to assume.
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sts:AssumeRole",
            "Resource": "arn:aws:iam::ACCOUNT_ID:role/YOUR-IAM-ROLE-NAME"
        }
    ]
}
```
### IAM Role - Trust Policy Update
Configure your IAM role with a trust policy to allow you(your IAM User) to assume that role,
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::ACCOUNT_ID:user/YOUR-IAM-USER-NAME"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Update IAM User AWS CLI Profile
A profile with which to assume the role
```sh
# Configures your AWS CLI to use the Role ARN and the credentials of your default profile
aws configure set profile.s3-data.role_arn arn:aws:iam::ACCOUNT_ID:user/YOUR-IAM-USER-NAME
aws configure set profile.s3-data.source_profile default

# Set of commands to quickly configure AWS CLI profile with name `s3-data`
# aws configure set --profile s3-data aws_access_key_id AFEBZKIAIKIQ
# aws configure set --profile s3-data aws_secret_access_key u1C5jt93obx9cvlF
# aws configure set --profile s3-data region eu-central-1

# if you want to configure the CLI to use different credentials for your Role, if the profile name is `s3-data`
# aws configure set profile.s3-data.source_profile s3-data
```

## Test IAM Role Access
Once all that is set up, you run some command. Let's say my role gives me S3 access, so I would do this:
```sh
> aws s3 ls --profile s3-data
2018-08-23 17:39:43 your-bucket-names-here
```
##### References
[1] - [AWS Docs - Role to Delegate Permissions to an IAM User](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-user.html)

[2] - [Github](https://github.com/aws/aws-cli/issues/2279)