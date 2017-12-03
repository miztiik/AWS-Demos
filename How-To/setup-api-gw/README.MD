# AWS API Gateway Demo
A small RESTful API to provide information about products. In this demo we are going to provide agricultural commodity information from a prebuilt python dictionary(_hard coded_)

![Fig 1 : API GW + Lambda=FrontEnd + BackEnd](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/img/API%20GW%20%2B%20Lambda%3DFrontEnd%20%2B%20BackEnd.png)
## Pre-Requisities
 - We will RHEL AMI
 - AWS CLI Installed and Configured
 -- For instructions to install `aws` cli refer [here](https://github.com/miztiik/AWS-Demos/tree/master/How-To/setup-aws-cli)
- IAM Lambda Service Role: `serverless-image-processor`
  - Permissions to `AWSS3FullAccess`
  - Permissions to `AWSLambdaExecute`
- S3 Bucket for API Code: `commodity-price-data`


_Note : You might not be able to use the same bucket names, so choose your own bucket names and use accordingly_


### Create Python Work Environment
Install the Boto3 package if it not there already - For packaging to lambda it is not necessary as it is provided by AWS by default, so we can install it outside our virtual environment. _If `pip` is not found install by following the instructions [here](https://github.com/miztiik/AWS-Demos/tree/master/How-To/setup-aws-cli)_

#### Setup Environment Variables
Set up environment variables describing the associated resources,
```sh
# Change to your own unique S3 bucket name:
awsRegion=ap-south-1
srcBucket=serverless-image-processor
destBucket=processed-image-data
funcName=commodity-price-data
lambda_exec_iam_role_name=${funcName}-role
lambda_exec_iam_role_name_arn=$(aws iam get-role --role-name ${lambda_exec_iam_role_name} --output text --query 'Role.Arn')
accountID=$(aws sts get-caller-identity --output text --query 'Account')
```


# Setup the AWS bash profile
```sh
export PATH=~/.local/bin:$PATH
source ~/.bash_profile
```

```sh
yum -y install zip
pip install boto3 virtualenv
virtualenv /var/${funcName}
cd /var/${funcName}
source bin/activate
pip install --upgrade pip
```
We will be using the python `Pillow` package for doing the image processing.
```sh
pip install flask jsonify flask_restful
pip freeze > requirements.txt
```

### Lets Package the bin for lambda
```sh
cd /var/${funcName}/lib/python2.7/site-packages
zip -r9 /var/${funcName}.zip *
```

### Image Resizing Code
The source, destination buckets needs to be updated to **your bucket names**
```sh
cat > /var/${funcName}/msp.py << "EOF"
from flask import Flask, jsonify, make_response

from flask_restful import Resource, Api
from json import dumps

app = Flask(__name__)
api = Api(app)


msp=[
{"CommodityNo":1, "CommodityName":"Paddy","Season":"Kharif","Variety":"Common","1998-99":"440","1999-00":"490","2000-01":"510","2001-02":"530","2002-03":"550","2003-04":"550","2004-05":"560","2005-06":"570","2006-07":"580","2007-08":"850","2008-09":"850","2009-10":"950","2010-11":"1000","2011-12":"1080","2012-13":"1250","2013-14":"1310","2014-15":"1360","2015-16":"1410","2016-17":"1470","2017-18":"1550"},
{"CommodityNo":2, "CommodityName":"Paddy","Season":"Kharif","Variety":"Grade 'A'","1998-99":"470","1999-00":"520","2000-01":"540","2001-02":"560","2002-03":"580","2003-04":"580","2004-05":"590","2005-06":"600","2006-07":"610","2007-08":"880","2008-09":"880","2009-10":"980","2010-11":"1030","2011-12":"1110","2012-13":"1280","2013-14":"1345","2014-15":"1400","2015-16":"1450","2016-17":"1510","2017-18":"1590"},
{"CommodityNo":3, "CommodityName":"Jowar","Season":"Kharif","Variety":"Hybrid","1998-99":"390","1999-00":"415","2000-01":"445","2001-02":"485","2002-03":"490","2003-04":"505","2004-05":"515","2005-06":"525","2006-07":"540","2007-08":"600","2008-09":"840","2009-10":"840","2010-11":"880","2011-12":"980","2012-13":"1500","2013-14":"1500","2014-15":"1530","2015-16":"1570","2016-17":"1625","2017-18":"1700"},
{"CommodityNo":4, "CommodityName":"Jowar","Season":"Kharif","Variety":"Maldandi","1998-99":"","1999-00":"","2000-01":"","2001-02":"","2002-03":"","2003-04":"","2004-05":"","2005-06":"","2006-07":"555","2007-08":"620","2008-09":"860","2009-10":"860","2010-11":"900","2011-12":"1000","2012-13":"1520","2013-14":"1520","2014-15":"1550","2015-16":"1590","2016-17":"1650","2017-18":"1725"},
{"CommodityNo":5, "CommodityName":"Bajra","Season":"Kharif","Variety":"","1998-99":"390","1999-00":"415","2000-01":"445","2001-02":"485","2002-03":"495","2003-04":"505","2004-05":"515","2005-06":"525","2006-07":"540","2007-08":"600","2008-09":"840","2009-10":"840","2010-11":"880","2011-12":"980","2012-13":"1175","2013-14":"1250","2014-15":"1250","2015-16":"1275","2016-17":"1330","2017-18":"1425"},
{"CommodityNo":6, "CommodityName":"Maize","Season":"Kharif","Variety":"","1998-99":"390","1999-00":"415","2000-01":"445","2001-02":"485","2002-03":"490","2003-04":"505","2004-05":"525","2005-06":"540","2006-07":"540","2007-08":"620","2008-09":"840","2009-10":"840","2010-11":"880","2011-12":"980","2012-13":"1175","2013-14":"1310","2014-15":"1310","2015-16":"1325","2016-17":"1365","2017-18":"1425"},
{"CommodityNo":7, "CommodityName":"Ragi","Season":"Kharif","Variety":"","1998-99":"390","1999-00":"415","2000-01":"445","2001-02":"485","2002-03":"490","2003-04":"505","2004-05":"515","2005-06":"525","2006-07":"540","2007-08":"600","2008-09":"915","2009-10":"915","2010-11":"965","2011-12":"1050","2012-13":"1500","2013-14":"1500","2014-15":"1550","2015-16":"1650","2016-17":"1725","2017-18":"1900"},
{"CommodityNo":8, "CommodityName":"Arhat(Tur)","Season":"Kharif","Variety":"","1998-99":"960","1999-00":"1105","2000-01":"1200","2001-02":"1320","2002-03":"1325","2003-04":"1360","2004-05":"1390","2005-06":"1400","2006-07":"1410","2007-08":"1550","2008-09":"2000","2009-10":"2300","2010-11":"3000","2011-12":"3200","2012-13":"3850","2013-14":"4300","2014-15":"4350","2015-16":"4625","2016-17":"5050","2017-18":"5450"},
{"CommodityNo":9, "CommodityName":"Moong","Season":"Kharif","Variety":"","1998-99":"960","1999-00":"1105","2000-01":"1200","2001-02":"1320","2002-03":"1335","2003-04":"1370","2004-05":"1410","2005-06":"1520","2006-07":"1520","2007-08":"1700","2008-09":"2520","2009-10":"2760","2010-11":"3170","2011-12":"3500","2012-13":"4400","2013-14":"4500","2014-15":"4600","2015-16":"4850","2016-17":"5225","2017-18":"5575"},
{"CommodityNo":10,"CommodityName":"Urad","Season":"Kharif","Variety":"","1998-99":"960","1999-00":"1105","2000-01":"1200","2001-02":"1320","2002-03":"1335","2003-04":"1370","2004-05":"1410","2005-06":"1520","2006-07":"1520","2007-08":"1700","2008-09":"2520","2009-10":"2520","2010-11":"2900","2011-12":"3300","2012-13":"4300","2013-14":"4300","2014-15":"4350","2015-16":"4625","2016-17":"5000","2017-18":"5400"},
{"CommodityNo":11,"CommodityName":"Cotton","Season":"Kharif","Variety":"F-414/H-177/J34","1998-99":"1440","1999-00":"1575","2000-01":"1625","2001-02":"1675","2002-03":"1695","2003-04":"1725","2004-05":"1760","2005-06":"1760","2006-07":"1770","2007-08":"1800","2008-09":"2500","2009-10":"2500","2010-11":"2500","2011-12":"2800","2012-13":"3600","2013-14":"3700","2014-15":"3750","2015-16":"3800","2016-17":"3860","2017-18":"4020"},
{"CommodityNo":12,"CommodityName":"Cotton","Season":"Kharif","Variety":"H-4","1998-99":"1650","1999-00":"1775","2000-01":"1825","2001-02":"1875","2002-03":"1895","2003-04":"1925","2004-05":"1960","2005-06":"1980","2006-07":"1990","2007-08":"2030","2008-09":"3000","2009-10":"3000","2010-11":"3000","2011-12":"3300","2012-13":"3900","2013-14":"4000","2014-15":"4050","2015-16":"4100","2016-17":"4160","2017-18":"4320"},
{"CommodityNo":13,"CommodityName":"GroundnutInShell","Season":"Kharif","Variety":"","1998-99":"1040","1999-00":"1155","2000-01":"1220","2001-02":"1340","2002-03":"1375","2003-04":"1400","2004-05":"1500","2005-06":"1520","2006-07":"1520","2007-08":"1550","2008-09":"2100","2009-10":"2100","2010-11":"2300","2011-12":"2700","2012-13":"3700","2013-14":"4000","2014-15":"4000","2015-16":"4030","2016-17":"4220","2017-18":"4450"},
{"CommodityNo":14,"CommodityName":"SunflowerSeed","Season":"Kharif","Variety":"","1998-99":"1060","1999-00":"1155","2000-01":"1170","2001-02":"1185","2002-03":"1325","2003-04":"1500","2004-05":"1340","2005-06":"1500","2006-07":"1500","2007-08":"1510","2008-09":"2215","2009-10":"2215","2010-11":"2350","2011-12":"2800","2012-13":"3700","2013-14":"3700","2014-15":"3750","2015-16":"3800","2016-17":"3950","2017-18":"4100"},
{"CommodityNo":15,"CommodityName":"Soyabeen","Season":"Kharif","Variety":"Black","1998-99":"705","1999-00":"755","2000-01":"775","2001-02":"795","2002-03":"805","2003-04":"840","2004-05":"900","2005-06":"900","2006-07":"900","2007-08":"910","2008-09":"1350","2009-10":"1350","2010-11":"1400","2011-12":"1650","2012-13":"2200","2013-14":"2500","2014-15":"2500","2015-16":"","2016-17":"","2017-18":""},
{"CommodityNo":16,"CommodityName":"Soyabeen","Season":"Kharif","Variety":"Yellow","1998-99":"795","1999-00":"845","2000-01":"865","2001-02":"885","2002-03":"895","2003-04":"930","2004-05":"1000","2005-06":"1010","2006-07":"1020","2007-08":"1050","2008-09":"1390","2009-10":"1390","2010-11":"1440","2011-12":"1690","2012-13":"2240","2013-14":"2560","2014-15":"2560","2015-16":"2600","2016-17":"2775","2017-18":"3050"},
{"CommodityNo":17,"CommodityName":"Sesamum","Season":"Kharif","Variety":"","1998-99":"1060","1999-00":"1205","2000-01":"1300","2001-02":"1400","2002-03":"1455","2003-04":"1485","2004-05":"1500","2005-06":"1550","2006-07":"1560","2007-08":"1580","2008-09":"2750","2009-10":"2850","2010-11":"2900","2011-12":"3400","2012-13":"4200","2013-14":"4500","2014-15":"4600","2015-16":"4700","2016-17":"5000","2017-18":"5300"},
{"CommodityNo":18,"CommodityName":"Nigerseed","Season":"Kharif","Variety":"","1998-99":"850","1999-00":"915","2000-01":"1025","2001-02":"1100","2002-03":"1120","2003-04":"1155","2004-05":"1180","2005-06":"1200","2006-07":"1220","2007-08":"1240","2008-09":"2405","2009-10":"2405","2010-11":"2450","2011-12":"2900","2012-13":"3500","2013-14":"3500","2014-15":"3600","2015-16":"3650","2016-17":"3825","2017-18":"4050"},
{"CommodityNo":19,"CommodityName":"Wheat","Season":"Rabi","Variety":"","1998-99":"550","1999-00":"580","2000-01":"610","2001-02":"620","2002-03":"630","2003-04":"630","2004-05":"640","2005-06":"650","2006-07":"750","2007-08":"1000","2008-09":"1080","2009-10":"1100","2010-11":"1120","2011-12":"1285","2012-13":"1350","2013-14":"1400","2014-15":"1450","2015-16":"1525","2016-17":"1625","2017-18":""},
{"CommodityNo":20,"CommodityName":"Barley","Season":"Rabi","Variety":"","1998-99":"385","1999-00":"430","2000-01":"500","2001-02":"500","2002-03":"505","2003-04":"525","2004-05":"540","2005-06":"550","2006-07":"565","2007-08":"650","2008-09":"680","2009-10":"750","2010-11":"780","2011-12":"980","2012-13":"980","2013-14":"1100","2014-15":"1150","2015-16":"1225","2016-17":"1325","2017-18":""},
{"CommodityNo":21,"CommodityName":"Gram","Season":"Rabi","Variety":"","1998-99":"895","1999-00":"1015","2000-01":"1100","2001-02":"1200","2002-03":"1225","2003-04":"1400","2004-05":"1425","2005-06":"1435","2006-07":"1445","2007-08":"1600","2008-09":"1730","2009-10":"1760","2010-11":"2100","2011-12":"2800","2012-13":"3000","2013-14":"3100","2014-15":"3175","2015-16":"3500","2016-17":"4000","2017-18":""},
{"CommodityNo":22,"CommodityName":"Masur(Lentil)","Season":"Rabi","Variety":"","1998-99":"","1999-00":"","2000-01":"1200","2001-02":"1300","2002-03":"1325","2003-04":"1500","2004-05":"1525","2005-06":"1535","2006-07":"1545","2007-08":"1700","2008-09":"1870","2009-10":"1870","2010-11":"2250","2011-12":"2800","2012-13":"2900","2013-14":"2950","2014-15":"3075","2015-16":"3400","2016-17":"3950!","2017-18":""},
{"CommodityNo":23,"CommodityName":"Rapeseed/Mustard","Season":"Rabi","Variety":"","1998-99":"1000","1999-00":"1100","2000-01":"1200","2001-02":"1300","2002-03":"1340","2003-04":"1600","2004-05":"1700","2005-06":"1715","2006-07":"1715","2007-08":"1800","2008-09":"1830","2009-10":"1830","2010-11":"1850","2011-12":"2500","2012-13":"3000","2013-14":"3050","2014-15":"3100","2015-16":"3350","2016-17":"3700","2017-18":""},
{"CommodityNo":24,"CommodityName":"Safflower","Season":"Rabi","Variety":"","1998-99":"990","1999-00":"1100","2000-01":"1200","2001-02":"1300","2002-03":"1305","2003-04":"1500","2004-05":"1550","2005-06":"1565","2006-07":"1565","2007-08":"1650","2008-09":"1650","2009-10":"1680","2010-11":"1800","2011-12":"2500","2012-13":"2800","2013-14":"3000","2014-15":"3050","2015-16":"3300","2016-17":"3700","2017-18":""},
{"CommodityNo":25,"CommodityName":"Toria","Season":"Rabi","Variety":"","1998-99":"965","1999-00":"1065","2000-01":"1165","2001-02":"1265","2002-03":"1305","2003-04":"1565","2004-05":"1665","2005-06":"1680","2006-07":"1680","2007-08":"1735","2008-09":"1735","2009-10":"1735","2010-11":"1780","2011-12":"2425","2012-13":"2970","2013-14":"3020","2014-15":"3020","2015-16":"3290","2016-17":"-","2017-18":""},
{"CommodityNo":26,"CommodityName":"Copra","Season":"OtherCrops","Variety":"Milling","1998-99":"2900","1999-00":"3100","2000-01":"3250","2001-02":"3300","2002-03":"3300","2003-04":"3320","2004-05":"3500","2005-06":"3570","2006-07":"3590","2007-08":"3620","2008-09":"3660","2009-10":"4450","2010-11":"4450","2011-12":"4525","2012-13":"5100","2013-14":"5250","2014-15":"5250","2015-16":"5550","2016-17":"5950","2017-18":""},
{"CommodityNo":27,"CommodityName":"Copra","Season":"OtherCrops","Variety":"Ball","1998-99":"3125","1999-00":"3325","2000-01":"3500","2001-02":"3550","2002-03":"3550","2003-04":"3570","2004-05":"3750","2005-06":"3820","2006-07":"3840","2007-08":"3870","2008-09":"3910","2009-10":"4700","2010-11":"4700","2011-12":"4775","2012-13":"5350","2013-14":"5500","2014-15":"5500","2015-16":"5830","2016-17":"6240","2017-18":""},
{"CommodityNo":28,"CommodityName":"De-HuskedCoconut","Season":"OtherCrops","Variety":"","1998-99":"","1999-00":"","2000-01":"","2001-02":"","2002-03":"","2003-04":"","2004-05":"","2005-06":"","2006-07":"","2007-08":"","2008-09":"988","2009-10":"1200","2010-11":"1200","2011-12":"1200","2012-13":"1400","2013-14":"1425","2014-15":"1425","2015-16":"1500","2016-17":"1600","2017-18":""},
{"CommodityNo":29,"CommodityName":"Jute","Season":"OtherCrops","Variety":"TD-5","1998-99":"650","1999-00":"750","2000-01":"785","2001-02":"810","2002-03":"850","2003-04":"860","2004-05":"890","2005-06":"910","2006-07":"1000","2007-08":"1055","2008-09":"1250","2009-10":"1375","2010-11":"1575","2011-12":"1675","2012-13":"2200","2013-14":"2300","2014-15":"2400","2015-16":"2700","2016-17":"3200","2017-18":""},
{"CommodityNo":30,"CommodityName":"Sugarcane","Season":"OtherCrops","Variety":"","1998-99":"52.7","1999-00":"56.1","2000-01":"59.5","2001-02":"62.05","2002-03":"69.5","2003-04":"73","2004-05":"74.5","2005-06":"79.5","2006-07":"80.25","2007-08":"81.18","2008-09":"81.18","2009-10":"129.84","2010-11":"139.12","2011-12":"145","2012-13":"170","2013-14":"210","2014-15":"220","2015-16":"230","2016-17":"230","2017-18":""},
{"CommodityNo":31,"CommodityName":"Tobacco","Season":"OtherCrops","Variety":"Black Soil(F2 Gr)","1998-99":"22.5","1999-00":"25","2000-01":"26","2001-02":"27","2002-03":"28","2003-04":"31","2004-05":"32","2005-06":"32","2006-07":"32","2007-08":"32","2008-09":"","2009-10":"","2010-11":"","2011-12":"","2012-13":"","2013-14":"","2014-15":"","2015-16":"","2016-17":"","2017-18":""},
{"CommodityNo":32,"CommodityName":"Tobacco","Season":"OtherCrops","Variety":"Light Soil (L2 Gr)","1998-99":"25.5","1999-00":"27","2000-01":"28","2001-02":"29","2002-03":"30","2003-04":"33","2004-05":"34","2005-06":"34","2006-07":"34","2007-08":"34","2008-09":"","2009-10":"","2010-11":"","2011-12":"","2012-13":"","2013-14":"","2014-15":"","2015-16":"","2016-17":"","2017-18":""},
{"CommodityNo":33,"CommodityName":"SunflowerSeed","Season":"OtherCrops","Variety":"","1998-99":"","1999-00":"","2000-01":"","2001-02":"","2002-03":"1210","2003-04":"1250","2004-05":"1340","2005-06":"","2006-07":"","2007-08":"","2008-09":"","2009-10":"","2010-11":"","2011-12":"","2012-13":"","2013-14":"","2014-15":"","2015-16":"","2016-17":"","2017-18":""}
]

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Commodity Not found'}), 404)


class CommodityInfo(Resource):
    def get(self, commName):
        commodity = [item for item in msp if item['CommodityName'] == commName]
        if not commodity:
            not_found(404)
        return jsonify(commodity)

api.add_resource(CommodityInfo,'/api/v1.0/CommodityInfo/<commName>', methods=['GET'])

# flask run --host=0.0.0.0
if __name__ == '__main__':
     app.run()
EOF
```

### Add our `msp.py` to the zip file
```sh
cd /var/${funcName}
zip -g /var/${funcName}.zip msp.py
```

#### Upload zip file to S3 bucket
```sh
aws s3 cp /var/${funcName}.zip s3://commodity-price-data
```
_The URI for the s3 object should be something like and the size should be ~ **5 MB**_
```sh
https://s3.ap-south-1.amazonaws.com/commodity-price-data/commodity-price-data.zip
```

Copy the url `https://s3.ap-south-1.amazonaws.com/commodity-price-data/commodity-price-data.zip` from s3 and update the lambda function configuration

### Create the Lambda Function
You may find it easier to do the below steps from the GUI console, But be sure to provide the same values,

```sh
aws lambda create-function \
--description "This function creates an endpoint to provide agricultural commodity prices" \
--region ${awsRegion} \
--function-name ${funcName} \
--code S3Bucket=commodity-price-data,S3Key=${funcName}.zip \
--role ${lambda_exec_iam_role_name_arn} \
--handler msp.handler \
--runtime python2.7 \
--timeout 10 \
--memory-size 128
```

#### Add Lambda Permissions to receive trigger notifications
```sh
aws lambda add-permission \
--function-name ${funcName} \
--region ${awsRegion} \
--statement-id some-unique-id \
--action "lambda:InvokeFunction" \
--principal s3.amazonaws.com \
--source-arn arn:aws:s3:::${srcBucket} \
--source-account ${accountID}
```

#### Create S3 Notifications to trigger Lambda
```sh
# Get the Lambda ARN
lambda_function_arn=$(aws lambda get-function-configuration \
  --function-name "${funcName}" \
  --output text \
  --region ${awsRegion} \
  --query 'FunctionArn'
)

# Set the notification in S3 Bucket
aws s3api put-bucket-notification \
  --bucket ${srcBucket} \
  --notification-configuration '{
    "CloudFunctionConfiguration": {
      "CloudFunction": "'${lambda_function_arn}'",
      "Event": "s3:ObjectCreated:*"
    }
  }'
```

### Test the function
Go ahead and upload an object to your S3 source bucket and you should be able to find smaller images in the destination bucket after few seconds. _Allow few seconds for the lambda function to run:)_