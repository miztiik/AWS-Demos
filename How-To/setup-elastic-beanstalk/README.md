# Deploy a Flask Application to AWS Elastic Beanstalk

To follow this tutorial, you should have all of the Common Prerequisites for Python installed, including the following packages:

- Python 2.7
- pip
- virtualenv
- awsebcli


## Setup the development environment
#### The below commands have been tested in `RHEL`
```sh
## Install Elastic Beanstalk CLI
pip install --upgrade --user awsebcli
export PATH=/root/.local/bin:$PATH
source ~/.bashrc
#### Check the installation
eb --version

# Optionally upgrade `pip
# yum -y install python-pip
pip install --upgrade pip
pip install virtualenv
```


#### Create a Python Virtual Environment for our Applicaion
```sh
virtualenv /var/eb-virt
source /var/eb-virt/bin/activate
```

#### Install Flask
```sh
pip install flask==0.10.1
```
#### Verify `flask` installation
```sh
(newsapp)[root@ip var]# pip freeze
Flask==0.10.1
itsdangerous==0.24
Jinja2==2.9.6
MarkupSafe==1.0
Werkzeug==0.12.2
```

#### DEVELOP - Write the flask code
We are going to create a simple RESTful web service to welcome our user using python `flask` web framework
```sh
source /var/eb-virt/bin/activate
cd /var/eb-virt
mkdir newsapp

cat > "/var/eb-virt/newsapp/application.py" << "EOF"
from flask import Flask

# print a nice greeting.
def say_hello(username = "Valaxy"):
    return '<p>Hello %s!</p>\n' % username

# some bits of text for the page.
header_text = '''
    <html>\n<head> <title>EB Flask Test</title> </head>\n<body>'''
instructions = '''
    <p><em>Hint</em>: This is a RESTful web service! Append a username
    to the URL (for example: <code>/Valaxy</code>) to say hello to
    someone specific.</p>\n'''
home_link = '<p><a href="/">Back</a></p>\n'
footer_text = '</body>\n</html>'

# EB looks for an 'application' callable by default.
application = Flask(__name__)

# add a rule for the index page.
application.add_url_rule('/', 'index', (lambda: header_text +
    say_hello() + instructions + footer_text))

# add a rule when the page is accessed with a name appended to the site
# URL.
application.add_url_rule('/<username>', 'hello', (lambda username:
    header_text + say_hello(username) + home_link + footer_text))

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()
EOF
```
#### Verirfy `app` directory structure
```sh
~]# tree -a /var/eb-virt/newsapp
/var/eb-virt/newsapp
├── application.py
└── requirements.txt
```

## BUILD - Lets Package the app
```sh
source /var/eb-virt/bin/activate
pip freeze > /var/eb-virt/newsapp/requirements.txt
deactivate
```

#### Create an Elastic Beanstalk Application environment 
Elastic Beanstalk create needs application cluster at the top level under which we can have multiple environments, say `dev`,`test` and `prod`
```sh
cd /var/eb-virt/newsapp
eb init -p python2.7 newsapp --region ap-south-1
```
#### Optional Set keypair for EC2 instances
```sh
eb init
```
### Check `eb` Configuration
```sh
eb config
```
## RELEASE - Deploy `application` to Elastic Bean Stalk
Lets go ahead and create an environment and deploy our app
```sh
eb create newsapp-env-prod
```

##### For testing in local browser
_This step will only work if you have X11 configured in your server and browser installed,_
```sh
eb open
```

## MONITOR - Configure Cloudwatch
We can configure cloudwatch to monitor our deplooyment and inform the devs of any potentital bugs and defects

## UPDATES - Pushing `app` updates to `eb`
Here we will learn how to perform `Blue-Green` deployments
```sh
eb deploy
```

### To switch between staging and production environment
List the current environment and we will use the `eb use` command to switch
```sh
# List environments
eb list
# eb use {{env-name}}
eb use newsapp-env-dev
```
### Clean Up and Next Steps
```sh
eb terminate newsapp-env-prod
```