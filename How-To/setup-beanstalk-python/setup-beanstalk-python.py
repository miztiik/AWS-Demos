#!/bin/bash
# setup-beanstalk-python



## Install Elastic Beanstalk CLI
pip install --upgrade --user awsebcli
export PATH=/root/.local/bin:$PATH
source ~/.bashrc
#### Check the installation
eb --version


## Set up your virtual environment
#### Create a virtual environment named eb-virt:
virtualenv ~/eb-virt
#### Activate the virtual environment:
source ~/eb-virt/bin/activate
#### Install flask
pip install flask==0.10.1

### Create Flask Application
mkdir eb-flask
cd eb-flask
touch application.py
cat >> application.py << "EOF"
from flask import Flask

# print a nice greeting.
def say_hello(username = "World"):
    return '<p>Hello %s!</p>\n' % username


# some bits of text for the page.
header_text = '''
    <html>\n<head> <title>EB Flask Test</title> </head>\n<body>'''
instructions = '''
    <p><em>Hint</em>: This is a RESTful web service! Append a username
    to the URL (for example: <code>/Miztiik</code>) to say hello to
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

### Configure your site for Elastic Beanstalk
source ~/eb-virt/bin/activate
##### Elastic Beanstalk uses to requirements.txt to determine which package to install on the EC2 instances that run your application.
pip freeze > requirements.txt
deactivate

## Deploy Your Site With the EB CLI
### Create an environment and deploy your Flask application
cd ~/eb-virt/eb-flask
eb init -p python2.7 miztiik-flask-demo
eb create flask-env
# For testing in local browser
eb open