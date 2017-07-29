# Create a User
```py
import boto3
```

# Create IAM client
```py
iam = boto3.client('iam')

# Create user
response = iam.create_user(
    UserName='Valaxy-Demo-User'
)

print(response)
```

# List Users in Your Account
```py
paginator = iam.get_paginator('list_users')
for response in paginator.paginate():
    print(response)
```

# Update a User's Name
```py
iam.update_user(
    UserName='Valaxy-Demo-User',
    NewUserName='Valaxy-User-01'
)
```

# Delete a user
```
iam.delete_user(
    UserName='Valaxy-User-01'
)
```
