# RDS Connections

## How to Connect to RDS from EC2
```sql
mysql -h myinstance.123456789012.us-east-1.rds.amazonaws.com -P 3306 -u dbmaster -p
```

### Retrieve the maximum number of connections allowed for an Amazon RDS

```sql
SELECT @@max_connections;
```

### You can retrieve the number of active connections to an Amazon RDS

```sql
SHOW STATUS WHERE `variable_name` = 'Threads_connected’;
```

### Show Databases
```sql
show databases;
use <database-name>
```

### Create Tables

#### We will create a students table with Student ID, Name & Address Columns

```sql
CREATE TABLE Students ( StudentID int, LastName varchar(255), FirstName varchar(255), City varchar(255) );


#### Insert records into tables
INSERT INTO Students ( StudentID, LastName, FirstName, City) VALUES ( "001", "Kumar", "Anil", "Singapore" );

INSERT INTO Students ( StudentID, LastName, FirstName, City) VALUES ( "002", "Reddy", "M", "Hyderabad" );

INSERT INTO Students ( StudentID, LastName, FirstName, City) VALUES ( "003", "Reddy", "N", "Hyderabad" );

INSERT INTO Students ( StudentID, LastName, FirstName, City) VALUES ( "004", "Vel", "D", "Chennai" );

INSERT INTO Students ( StudentID, LastName, FirstName, City) VALUES ( "005", "Student", "Martian", "Mars" );
```

### View the contents of the tables
```sql
select * from Students;
```

#### Making specific queries
```sql
select StudentID from Students WHERE (LastName="Reddy");
select StudentID,City from Students WHERE (LastName="Reddy");
```

### Deleting Tables
```sql
drop tables Students;
```

# Dynamo DB

Assuming you have a collection named `aws-students` - If not go ahead and create one.

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
Output:

{
    "ConsumedCapacity": {
        "CapacityUnits": 1.0,
        "TableName": "MusicCollection"
    }
```

##### Ref
[1] - [AWS Docs](http://docs.aws.amazon.com/cli/latest/reference/dynamodb/put-item.html)
