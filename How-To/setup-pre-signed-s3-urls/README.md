# S3 Security - Uploading Objects Using Pre-Signed URLs

Pre-signed URLs are useful if you want your user/customer to be able to upload a specific object to your bucket, but you don't require them to have AWS security credentials or permissions. When you create a pre-signed URL, you must provide your security credentials and then specify a bucket name, an object key, an HTTP method (PUT for uploading objects), and an expiration date and time. The pre-signed URLs are valid only for the specified duration.

You can generate a pre-signed URL programmatically, We will be using python SDK

![](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-pre-signed-s3-urls/images/signed-url-upload-flow.png)

Follow this article in **[Youtube](https://www.youtube.com/channel/UC_evcfxhjjui5hChhLE08tQ/playlists)**



##### References
[1] - [AWS Docs - Uploading Objects Using Pre-Signed URLs](https://docs.aws.amazon.com/AmazonS3/latest/dev/PresignedUrlUploadObject.html)

[2] - [Boto Docs - Generating Presigned URLs](https://boto3.readthedocs.io/en/latest/guide/s3.html#generating-presigned-urls)