# S3 Security - Uploading Objects Using Pre-Signed URLs

Pre-signed URLs are useful if you want your user/customer to be able to upload a specific object to your bucket, but you don't require them to have AWS security credentials or permissions. When you create a pre-signed URL, you must provide your security credentials and then specify a bucket name, an object key, an HTTP method (PUT for uploading objects), and an expiration date and time. The pre-signed URLs are valid only for the specified duration.

Follow this article in **[Youtube](https://youtu.be/IDoEERbTQm4)**

![](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-pre-signed-s3-urls/images/signed-url-upload-flow.png)

### Deploy the App
You can generate a pre-signed URL programmatically, We will be using python SDK. Here are the high level steps
1. Create S3 Bucket - `my-secure-pvt-bkt`
   - Enable `CORS` in bucket permission to add CORSRule `<AllowedMethod>POST</AllowedMethod>`
     - _For Production consider using Allowed Origin to be domain specific. Instead of "`*`"_
   - Upload the `index.html` to bucket and make it `Public`
1. Create IAM Role - `s3-pre-signer-lambda` [Get help here](https://www.youtube.com/watch?v=5g0Cuq-qKA0&index=11&list=PLxzKY3wu0_FLaF9Xzpyd9p4zRCikkD9lE)
   - Attach managed permissions - `AWSLambdaExecute`
1. Create Lambda - Function Name: `s3-pre-signer-lambda` [Get help here](https://www.youtube.com/watch?v=paNAQh3QA9E&list=PLxzKY3wu0_FJuyy7dUn5unlWmM7QuPo6e&index=4)
   - Attach the IAM Role
1. Create API GW - `s3-pre-signer-api` [Get help here](https://www.youtube.com/watch?v=uy6husQW7mM&list=PLxzKY3wu0_FJuyy7dUn5unlWmM7QuPo6e&index=8)
   - Create Method `POST`
     - Attach Lambda function as proxy
   - Enable CORS Support
   - Deploy API

### Launch the app
Open `index.html` url in your favorite browser,
![Secure-S3-Pre-Signed-Url-Uploader](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/How-To/setup-pre-signed-s3-urls/images/Screenshot-Valaxy-Miztiik.png)

##### References
[1] - [AWS Docs - Uploading Objects Using Pre-Signed URLs](https://docs.aws.amazon.com/AmazonS3/latest/dev/PresignedUrlUploadObject.html)

[2] - [Boto Docs - Generating Presigned URLs](https://boto3.readthedocs.io/en/latest/guide/s3.html#generating-presigned-urls)