# Deploying a Flask Application to AWS Elastic Beanstalk

To follow this tutorial, you should have all of the Common Prerequisites for Python installed, including the following packages:

- Python 2.7
- pip
- virtualenv
- awsebcli

## Setup the development environment
```sh
yum -y install python-pip
pip install --upgrade pip
pip install virtualenv
# Install Flask
pip install flask==0.10.1
pip freeze

## Install Elastic Beanstalk CLI
pip install --upgrade --user awsebcli
export PATH=/root/.local/bin:$PATH
source ~/.bashrc
#### Check the installation
eb --version
```


## Create a Python Virtual Environment for our Applicaion
```sh
mkdir -p /var/virt-env/elastic-bean-stalk-app
virtualenv /var/virt-env/
source /var/virt-env/bin/activate
```

### Install Flask
```sh
pip install flask
```
#### DEV - Write the flask code
We are creating a simple flask application to welcome our user
```sh
cd /var/virt-env/elastic-bean-stalk-app

cat > "/var/virt-env/elastic-bean-stalk-app/application.py" << "EOF"
from flask import Flask

# print the welcome greeting.
def say_hello(username = "World"):
    return '<p>Hello %s!</p>\n' % username

# some bits of text for the page.
header_text = '''
    <html>\n<head> <title>Valaxy ELastic Bean Stalk Demo<title> </head>\n<body>'''
instructions = '''
    <p><em>Hint</em>: This is a RESTful web service create by Valaxy Infotech! Append a username
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

## BUILD - Lets Package the app
```sh
source /var/virt-env/bin/activate
pip freeze > requirements.txt
deactivate
```
#### Create an `eb` environment and deploy our flask application
```sh
cd /var/virt-env/elastic-bean-stalk-app
eb init -p python2.7 prod-env-newsapp
```
#### Optional Set keypair for EC2 instances
```sh
eb init
```
## RELEASE - Deploy `application` to Elastic Bean Stalk
```sh
eb create newsapp
```

##### For testing in local browser
_This step will only work if you have X11 configured in your server and browser installed_
```sh
eb open
```
### Clean Up and Next Steps
```sh
eb terminate newsapp
```
