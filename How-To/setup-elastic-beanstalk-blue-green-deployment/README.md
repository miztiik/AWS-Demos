# Deploy application to AWS Elastic Beanstalk

To follow this tutorial, you should have all of the Common Prerequisites for Python installed, including the following packages:

- EC2 running Redhat Linux
- Python 2.7
- pip
- virtualenv
- awsebcli


## Setup the development environment
#### The below commands have been tested in `RHEL`
```sh

# Install pip in RHEL
yum -y install git
cd /tmp
curl -O https://bootstrap.pypa.io/get-pip.py
python get-pip.py --user
pip install --upgrade pip

#### Include the path in your profile
export PATH=/root/.local/bin:$PATH
source ~/.bash_profile

## Install Elastic Beanstalk CLI
pip install --upgrade --user awsebcli
export PATH=/root/.local/bin:$PATH
source ~/.bashrc
#### Check the installation
eb --version
#### Install the Python Virtual Environment Package
pip install virtualenv
```


#### Create a Python Virtual Environment for our Applicaion
```sh
virtualenv /var/eb-virt
cd /var/eb-virt
source /var/eb-virt/bin/activate
```

#### Clone the application repository
```sh
git clone https://github.com/miztiik/flask-news-app.git

# The below tagged release is expected to work perfectly in Elastic Beanstalk
# git reset --hard "v2.1"
```

#### Verirfy `app` directory structure
```sh
(eb-virt) [root@ip flask-news-app]# tree /var/eb-virt/flask-news-app
/var/eb-virt/flask-news-app
├── application.py
├── Dockerfile
├── pylintrc
├── README.md
├── requirements.txt
├── setup.sh
├── static
│   ├── css
│   │   └── main.css
│   └── favicon.ico
├── templates
│   ├── hotNews.html
│   └── welcome.html
└── tests
    └── test_app.py

4 directories, 11 files
```

## BUILD - Lets Package the app
#### Elastic Beanstalk create needs application cluster at the top level under which we can have multiple environments, say `dev`,`test` and `prod`
_The below step assumes you have AWS CLI configured. If not use the `aws configure` command with access key and secure key_
```sh
cd /var/eb-virt/flask-news-app
eb init -p python2.7 newsapp --region ap-south-1
```
#### Optional Set keypair for EC2 instances
```sh
eb init
```

## RELEASE - Deploy `application` to Elastic Bean Stalk
Lets go ahead and create an environment and deploy our app
```sh
eb create newsapp-env-prod
```
_Safely quit the rolling logs, when you see `-- Events -- (safe to Ctrl+C) Use "eb abort" to cancel the command.`_

### Check the status of the deployment
```sh
[root@ip flask-news-app]# eb status
Environment details for: newsapp-env-prod
  Application name: newsapp
  Region: ap-south-1
  Deployed Version: app-7fb8-170808_105240
  Environment ID: e-irxw3zwpcd
  Platform: arn:aws:elasticbeanstalk:ap-south-1::platform/Python 2.7 running on 64bit Amazon Linux/2.4.2
  Tier: WebServer-Standard
  CNAME: newsapp-env-prod.89tzx3rxs4.ap-south-1.elasticbeanstalk.com
  Updated: 2017-08-08 10:56:13.741000+00:00
  Status: Ready
  Health: Green
```
To list the current configuration,
```sh
eb config
```
### For testing in local browser
_This step will only work if you have X11 configured in your server and browser installed,_
```sh
eb open
```
##### AWS Elastic Beanstalk Applications page
![Fig 1 : AWS Elastic Beanstalk - Application(s)](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/img/Valaxy-Training-Elastic-Beanstalk-Application-Environments.png)
##### Applications Welcome page
![Fig 2 : Application - Welcome Page](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/img/valaxy-Training-Elastic-Beanstalk-Application-Environments-welcome.png)

##### Choose your 'newssection' to get news
![Fig 3 : Application - News Section Page](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/img/Valaxy-Training-Elastic-Beanstalk-Application-Environments-newssection.png)
##### The News Results from various resources are listed
![Fig 4 : Application - News Results Page](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/img/valaxy-Training-Elastic-Beanstalk-Application-Environments-news.png)
## MONITOR - Configure Cloudwatch
We can configure cloudwatch to monitor our deplooyment and inform the devs of any potentital bugs and defects

## UPDATES - [Blue / Green Deployments](http://docs.aws.amazon.com/elasticbeanstalk/latest/dg/using-features.CNAMESwap.html)

Here we will learn how to perform `Blue-Green` deployments. Make some _cosmetic changes_ to the `templates/welcome.html` file and commit the changes using `git` command.
```sh
cd /var/eb-virt/flask-news-app
git add .
git commit -m "Cosmetic Changes to the welcome template"
```

### Deploy to new environment
```sh
eb create newsapp-env-prod-blue
```


### To switch between staging and production environment
List the current environment and we will use the `eb use` command to switch
```sh
# List environments
[root@ip flask-news-app]# eb list --verbose
Region: ap-south-1
Application: newsapp
    Environments: 3
      * newsapp-env-prod : ['i-08daad2f61108abb6']
        newsapp-env-prod-blue : ['i-09f5735cb7f09d17c']


# eb use {{env-name}}
eb use newsapp-env-prod-blue
```
### Clean Up and Next Steps
_if you want to remove only some of the environments,_
```sh
eb terminate newsapp-env-prod
```

### Clean Up EB Application and all environments
```sh
eb terminate --all
```
The output should look like,
```sh
[root@ip flask-news-app]# eb terminate --all

The application "newsapp" and all its resources will be deleted.
This application currently has the following:
Running environments: 2
Configuration templates: 0
Application versions: 4

To confirm, type the application name: newsapp
Removing application versions from s3.
INFO: deleteApplication is starting.
INFO: Invoking Environment Termination workflows.
INFO: Terminate environment has already started.
 -- Events -- (safe to Ctrl+C)
```