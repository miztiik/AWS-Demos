# RDS Connections

## Install MySQL/MariaDB Client
Copy paste the below in the EC2 `user-data` field
```sh
#!/bin/bash
yum -y install mariadb
```

## How to Connect to RDS from EC2
```sql
mysql -h <Your-RDS-Endpoint> -P 3306 -u dbmaster -p
# For Example,
mysql -h myinstance.123456789012.us-east-1.rds.amazonaws.com -P 3306 -u dbmaster -p
```
If the above is giving errors, try disabling `selinux` by issuing this command `setenforce 0` to troubleshoot the issue. Once you are set, reenable `SELinux` with the appropriate privileges.

Another area to be sure is to get the `AWS Security Groups` to allow traffic on port `3306` from your `Source IP` or `web-app Security Group` 

### Show Databases
```sql
show databases;
use <database-name>
```

### You can retrieve the number of active connections to an Amazon RDS

```sql
SHOW STATUS WHERE `variable_name` = 'Threads_connected’;
```

### Retrieve the maximum number of connections allowed for an Amazon RDS

```sql
SELECT @@max_connections;
```

We will look into `CRUD` basics now,

### Create Tables

#### We will create a `Students` table with `Student ID, Name & City` as Columns

```sql
CREATE TABLE Students ( StudentID int, LastName varchar(255), FirstName varchar(255), City varchar(255) );
```

#### Insert records into tables
```sql
INSERT INTO Students ( StudentID, LastName, FirstName, City) VALUES ( "001", "Kumar", "Anil", "Singapore" );

INSERT INTO Students ( StudentID, LastName, FirstName, City) VALUES ( "002", "Reddy", "M", "Hyderabad" );

INSERT INTO Students ( StudentID, LastName, FirstName, City) VALUES ( "003", "Reddy", "N", "Hyderabad" );

INSERT INTO Students ( StudentID, LastName, FirstName, City) VALUES ( "004", "Vel", "D", "Chennai" );

INSERT INTO Students ( StudentID, LastName, FirstName, City) VALUES ( "005", "Student", "Martian", "Mars" );
```

### Retrieve records from table
```sql
select * from Students;
```

#### Making specific queries
```sql
select StudentID from Students WHERE (LastName="Reddy");
select StudentID,City from Students WHERE (LastName="Reddy");
```

### Delete Tables
```sql
drop tables Students;
```

# Dynamo DB

Assuming you have a collection named `aws-students` - If not go ahead and create one, with the following instructions:
- Create a new table `aws-students`
- Set the _Partition Key_ to `studentId` and Choose type as _**String**_
- For _Table Settings_, Use `Default Settings`
- Click _Create_

Lets get into **CRUD** - **C**reate, **R**etrieve, **U**pdate, **D**elete.

###### _You will need an EC2/linux client with `aws cli` configured to run the below commands_


### Create `item`
Lets create four student records(as json files) that will be inserted to the DynamoDB Collection called `aws-students` using `aws cli` command `put-item`
```sh
cat > "student001.json" << "EOF"
{"studentId":{"S":"1"},"studentDetails":{"S":"[{Name:'John Doe',Age:21,Sex:Male}]"}}
EOF

cat > "student002.json" << "EOF"
{"studentId":{"S":"2"},"studentDetails":{"S":"[{Name:'Jane Doe',Age:18,Sex:Female}]"}}
EOF

cat > "student003.json" << "EOF"
{"studentId":{"S":"3"},"studentDetails":{"S":"[{Name:'Old Mike',Age:881,Sex:''}]"}}
EOF

cat > "student004.json" << "EOF"
{"studentId":{"S":"4"},"studentDetails":{"S":"[{Name:'Young Mike',Age:18,Sex:}]"}}
EOF
```

Import the json using the below command
```nosql
aws dynamodb put-item --table-name aws-students --item file://student001.json --return-consumed-capacity TOTAL
aws dynamodb put-item --table-name aws-students --item file://student002.json --return-consumed-capacity TOTAL
aws dynamodb put-item --table-name aws-students --item file://student003.json --return-consumed-capacity TOTAL
aws dynamodb put-item --table-name aws-students --item file://student004.json --return-consumed-capacity TOTAL
```

#### Since i am lazy, I do this instead,
```sh
for i in {1..4}
do
  aws dynamodb put-item --table-name aws-students --item file://student00$i.json --return-consumed-capacity TOTAL
done
```

##### Output
```sh
{
    "ConsumedCapacity": {
        "CapacityUnits": 1.0, 
        "TableName": "aws-students"
    }
}
```
## Retrieve `item` from collection
Lets see if _Old Mike_'s data had been correctly updated.
```sh
aws dynamodb get-item --table-name aws-students --key '{"studentId":{"S":"3"}}'
```

### Output
```sh
{
    "Item": {
        "studentId": {
            "S": "3"
        },
        "studentDetails": {
            "S": "[{Name:'Old Mike',Age:81,Sex:'Male'}]"
        }
    }
}
```

## Update `item` in Collection
Since _Old Mike_ age is incorrectly updated as `881`, Lets correct it.
```sh
cat > "student003.json" << "EOF"
{"studentId":{"S":"3"},"studentDetails":{"S":"[{Name:'Old Mike',Age:81,Sex:'Male'}]"}}
EOF
```
#### Run the `put-item` command
```sh
aws dynamodb put-item --table-name aws-students --item file://student003.json --return-consumed-capacity TOTAL
```

## Delete `item` from Collection
Old Mike is no longer a student with our organization, Lets go ahead and remove him.
```sh
aws dynamodb delete-item --table-name aws-students --key '{"studentId":{"S":"3"}}'
```

##### Ref
[1] - [AWS Docs](http://docs.aws.amazon.com/cli/latest/reference/dynamodb/put-item.html)

[2] - [Dynamo DB Get Item Docs](http://docs.aws.amazon.com/cli/latest/reference/dynamodb/get-item.html)
