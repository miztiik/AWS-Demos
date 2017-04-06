
# Creating Buckets
aws s3 mb s3://bucket-name


# Copies an object into a bucket. It grants read permissions on the object to everyone and full permissions (read, readacl, and writeacl) to the account associated with user@example.com.
aws s3 cp file.txt s3://my-bucket/ --grants read=uri=http://acs.amazonaws.com/groups/global/AllUsers full=emailaddress=user@example.com

# specify a non-default storage class (REDUCED_REDUNDANCY or STANDARD_IA) for objects that you upload to Amazon S3, use the --storage-class option
aws s3 cp file.txt s3://my-bucket/ --storage-class REDUCED_REDUNDANCY

# synchronizes the contents of an Amazon S3 folder named path in my-bucket with the current working directory. s3 sync updates any files that have a different size or modified time than files with the same name at the destination
aws s3 sync . s3://my-bucket/path

_The --exclude and --include options allow you to specify rules to filter the files or objects to be copied during the sync operation. By default, all items in a specified directory are included in the sync_

// Delete local file
$ rm ./MyFile1.txt

// Attempt sync without --delete option - nothing happens
$ aws s3 sync . s3://my-bucket/path

// Sync with deletion - object is deleted from bucket
$ aws s3 sync . s3://my-bucket/path --delete
delete: s3://my-bucket/path/MyFile1.txt

// Delete object from bucket
$ aws s3 rm s3://my-bucket/path/MySubdirectory/MyFile3.txt
delete: s3://my-bucket/path/MySubdirectory/MyFile3.txt

// Sync with deletion - local file is deleted
$ aws s3 sync s3://my-bucket/path . --delete
delete: MySubdirectory\MyFile3.txt

// Sync with Infrequent Access storage class
$ aws s3 sync . s3://my-bucket/path --storage-class STANDARD_IA

aws s3 sync . s3://my-bucket/path --exclude '*.txt' --include 'MyFile*.txt'
aws s3 sync . s3://my-bucket/path --exclude '*.txt' --include 'MyFile*.txt'

### Delete s3://my-bucket/path/MyFile.txt
$ aws s3 rm s3://my-bucket/path/MyFile.txt

### Delete s3://my-bucket/path and all of its contents
$ aws s3 rm s3://my-bucket/path --recursive