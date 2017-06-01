# Install Python, pip, and AWS Command Line Interface on Linux ( Redhat / CentOS )

## Install `pip`
```sh
cd /tmp
curl -O https://bootstrap.pypa.io/get-pip.py
python get-pip.py --user
```

#### Include the path in your profile
The PIP install location in Linux with pip (user mode) is `~/.local/bin`, so lets add it to our path
```sh
export PATH=~/.local/bin:$PATH
source ~/.bash_profile
```

### Verify that pip is installed correctly.
```sh
pip --version
```
##### If the above didn't work, you may have python3, try the below command
```sh
python3 get-pip.py --user
pip --version
```
You should see something like
```
pip 8.1.2 from ~/.local/lib/python3.4/site-packages (python 3.4)
```

## Install AWS CLI
```
pip install awscli --upgrade --user
```

### Check version of AWS CLI
```
aws --version
```

#### To configure aws cli run `aws configure`
