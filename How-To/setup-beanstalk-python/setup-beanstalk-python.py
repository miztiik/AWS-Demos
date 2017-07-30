curl -O https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm \
&& yum -y install epel-release-latest-7.noarch.rpm
yum -y install python-pip
pip install --upgrade pip
pip install virtualenv

## Install Elastic Beanstalk CLI
pip install --upgrade --user awsebcli
export PATH=/root/.local/bin:$PATH
source ~/.bashrc
#### Check the installation
eb --version



# Create a Virtual Environment for our App

mkdir -p /var/virt-env/elastic-bean-stalk-app

virtualenv /var/virt-env/
source /var/virt-env/bin/activate

# Install Flask
pip install flask

cd /var/virt-env/elastic-bean-stalk-app

cat > "/var/virt-env/elastic-bean-stalk-app/application.py" << "EOF"
from flask import Flask

# print a nice greeting.
def say_hello(username = "World"):
    return '<p>Hello %s!</p>\n' % username

# some bits of text for the page.
header_text = '''
    <html>\n<head> <title>ELastic Bean Stalk Demo<title> </head>\n<body>'''
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
    application.run(host='0.0.0.0')
EOF

# Lets Package the app
source /var/virt-env/bin/activate

## Deploy Your Site With the EB CLI
### Create an environment and deploy your Flask application
cd /var/virt-env/elastic-bean-stalk-app
eb init -p python2.7 prod-env-newsapp
# Optional Set keypair
eb init

eb create newsapp
# For testing in local browser
eb open

# Clean Up and Next Steps
eb terminate newsapp
