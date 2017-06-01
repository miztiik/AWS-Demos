# RDS Connections

## Install MySQL Client
```sh
yum -y install mariadb
```

## How to Connect to RDS from EC2
```sql
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

Assuming you have a collection named `aws-students` - If not go ahead and create one.

###### You will need an EC2 Instance with `aws cli` configured to run the below commands

### Insert item into collection

This example adds a new item to the `aws-students` table. Create the json object that will be imported

```sh
cat > "student001.json" << "EOF"
{
  "studentId": {
    "S": "1"
  },
  "studentDetails": {
    "S": "[{Name:John,Age:21,Sex:Male}]"
  }
}
EOF
```

Import the json using the below command
```nosql
aws dynamodb put-item --table-name aws-students --item file://student001.json --return-consumed-capacity TOTAL
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

##### Ref
[1] - [AWS Docs](http://docs.aws.amazon.com/cli/latest/reference/dynamodb/put-item.html)
