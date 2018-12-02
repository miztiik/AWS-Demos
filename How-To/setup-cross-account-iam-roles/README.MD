# Delegate Access Across AWS Accounts Using IAM Roles
Imagine that the `Prod` account is where live applications are managed, and the `Acc` where developers and testers can freely test applications.

In the `Acc` account, Lets say you have a IAM groups: `DevGroup`. Users in this groups have permissions to work in the `Acc` account. Sometimes, a developer must update the applications in the `Prod` account, say to S3 bucket called `list-prod-bkt-details-01`.

![Delegate Access Across AWS Accounts Using IAM Roles](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-cross-cccount-iam-roles/images/IAM-CROSS-ACCOUNT-ACCESS-DELEGATION.png)

This tutorial teaches you how to use a role to delegate access to resources that are in different AWS accounts that you own (`Prod` and `Acc`).

We will accomplish this in 3 simple steps,
1. Create an IAM role in your Prod account.
1. Create a user in your Acc account to assume that IAM role.
1. Establish cross-account trust and access from the user in the Acc account to the role in the Prod account.

You can also follow this article in **[Youtube](https://www.youtube.com/watch?v=U5nDPagdLPk&t=0s&list=PLxzKY3wu0_FKok5gI1v4g4S-g-PLaW9YD&index=23)**

### Prerequisites
- Two AWS Accounts and Account numbers
  - Acc Account Id - 1111 1111 1111
    - IAM Group `Dev Group`
    - IAM User[ex: UserName=`David`] member of `Dev Group` - [Get help here](https://www.youtube.com/watch?v=5g0Cuq-qKA0&index=11&list=PLxzKY3wu0_FLaF9Xzpyd9p4zRCikkD9lE)
    - AWS CLI configured for ACC Account User `David`
  - Prod Account Id - 2222 2222 2222
    - S3 Bucket in Prod Account
    - Bucket Name: `list-prod-bkt-details-01`


## Create Role in `Prod` Account
- Login to `Prod` Account
- In IAM console, choose `Roles`, and then choose `Create role`.
- For `Select type of trusted entity`, choose `Another AWS Account`.
  - **IMPORTANT**: Update `Acc` account ID field, Choose `Next: Permissions`
- Choose `AmazonS3FullAccess` for permissions
- Update Role Name `acc-to-read-prod-s3-bucket`
- Collect Role ARN - `arn:aws:iam::222222222222:role/acc-to-read-prod-s3-bucket`

## Grant `Acc` Users Access to the `Prod` Role
- Login to `Acc` Account
- Choose `Groups`, and then choose `DevGroup`
- Choose the `Permissions` tab, expand the `Inline Policies` section
  - To create one, `click here`.
- Choose `Custom Policy` and then choose `Select`
- Type `allow-assume-S3-role-in-prod`
- Add the following policy statement to allow the `AssumeRole` action on the `acc-to-read-prod-s3-bucket` role in the Prod account. 
  - Update your `Prod Account Id` in the policy
```json
{
  "Version": "2012-10-17",
  "Statement": {
    "Effect": "Allow",
    "Action": "sts:AssumeRole",
    "Resource": "arn:aws:iam::222222222222:role/acc-to-read-prod-s3-bucket"
  }
}
```
- Choose `Apply Policy`

## Test Access by Switching Roles Using AWS CLI
Lets test the cross account access from AWS CLI configured with user `David`'s Credentials.

```sh
aws sts assume-role --role-arn "arn:aws:iam::222222222222:role/acc-to-read-prod-s3-bucket" --role-session-name "David-ProdData"
```
If we are getting something similar as show below, we are all set.
Output
```sh
{
    "AssumedRoleUser": {
        "AssumedRoleId": "AKIAIOSFODNN7EXAMPLE:David-ProdUpdate",
        "Arn": "arn:aws:sts::222222222222:assumed-role/acc-to-read-prod-s3-bucket/David-ProdUpdate"
    },
    "Credentials": {
        "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        "SessionToken": "AQoDYXdzEGcaEXAMPLE2gsYULo+Im5ZEXAMPLEeYjs1M2FUIgIJx9tQqNMBEXAMPLE
CvSRyh0FW7jEXAMPLEW+vE/7s1HRpXviG7b+qYf4nD00EXAMPLEmj4wxS04L/uZEXAMPLECihzFB5lTYLto9dyBgSDy
EXAMPLE9/g7QRUhZp4bqbEXAMPLENwGPyOj59pFA4lNKCIkVgkREXAMPLEjlzxQ7y52gekeVEXAMPLEDiB9ST3Uuysg
sKdEXAMPLE1TVastU1A0SKFEXAMPLEiywCC/Cs8EXAMPLEpZgOs+6hz4AP4KEXAMPLERbASP+4eZScEXAMPLEsnf87e
NhyDHq6ikBQ==",
        "Expiration": "2014-12-11T23:08:07Z",
        "AccessKeyId": "AKIAIOSFODNN7EXAMPLE"
    }
}
```

#### Set the ENVIRONMENT Variables
Lets test our new credentials using AWS CLI

```sh
aws configure set profile.prod-s3.role_arn arn:aws:iam::222222222222:role/acc-to-read-prod-s3-bucket
# Update 'default' to your actual profile name, if needed.
aws configure set profile.prod-s3.source_profile default
```
The first command will create a new CLI profile called `prod-s3` and will append the given role_arn to `~/.aws/config`. The second command sets the `source_profile`, which references the `default` credentials profile so that you can use the same IAM user for `Acc` and `Prod`.


### Query S3 in `Prod` Account
By just adding the `--profile` parameter we can query the `Prod` account
```sh
aws s3 ls --profile prod-s3 s3://list-prod-bkt-details-01/
```


##### References
[1] - [AWS Docs - Delegate Access Across AWS Accounts Using IAM Roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/tutorial_cross-account-with-roles.html)

[2] - [AWS Docs - Access All Your Accounts by Using the AWS CLI](https://aws.amazon.com/blogs/security/how-to-use-a-single-iam-user-to-easily-access-all-your-accounts-by-using-the-aws-cli/)



