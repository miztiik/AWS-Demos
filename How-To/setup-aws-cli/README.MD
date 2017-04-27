# Install Python, pip, and the AWS Command Line Interface on Linux ( Redhat / CentOS )

```
cd /tmp
curl -O https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py --user
python get-pip.py --user
```
#### Install AWS CLI
```
pip install awscli --upgrade --user
```
#### Include the path in your profile
The AWS CLI install location - Linux with pip (user mode) is `~/.local/bin`, so lets add it to our path
```
export PATH=~/.local/bin:$PATH
source ~/.bash_profile
```


# Check version of AWS CLI
```
aws --version
```
