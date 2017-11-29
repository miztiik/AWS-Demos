# AWS ElasticSearch with Logstash(in EC2)

You can have your own VPC and run Elasticsearch and Logstash inside the VPC, but we are going to use a public version.
Lets setup up the EC2 Logstash
![Data Source > Filebeat > Logstash > Elasticsearch](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/img/DataSource-Filebeat-Logstash-ElasticSearch.png "Data Source > Filebeat > Logstash > Elasticsearch")
## Start EC2
- AMI: `RHEL 7`
- VPC: Internet access with  public IP, so we can connect to it.
  - Security Group: Open Ports `22`, `80`, `443`
- Instance Type: `t2.micro` works, but more resources the better.

### Install Java v8
Get the latest version of Open JDK from [http://openjdk.java.net/install/](http://openjdk.java.net/install/)
`javac` is needed for logstash plugins, so we need the `devel` packages as well.
```sh
yum -yy install java-1.8.0-openjdk
yum -yy install java-1.8.0-openjdk-devel
# Confirm version of java
java -version
```

#### Set Java version to the latest
```sh
alternatives --config java
```

## Install Logstash

### Configure LogStash Repo GPG Key
`rpm --import https://artifacts.elastic.co/GPG-KEY-elasticsearch`

### Configure Logstash Repo URL
```sh
cat > /etc/yum.repos.d/logstash.repo << "EOF"
[logstash-6.x]
name=Elastic repository for 6.x packages
baseurl=https://artifacts.elastic.co/packages/6.x/yum
gpgcheck=1
gpgkey=https://artifacts.elastic.co/GPG-KEY-elasticsearch
enabled=1
autorefresh=1
type=rpm-md
EOF
```

#### Install Logstash
```sh
yum -y install logstash
```

```sh
# Logstash `bin` location
# /usr/share/logstash/bin/logstash -t -f logstash-syslog.conf
export PATH=$PATH:/usr/share/logstash/bin/
source ~/.bash_profile
```

#### Install `logstash-beats-plugin`
```sh
/usr/share/logstash/bin/logstash-plugin install logstash-input-beats
```

# Install `Filebeat`
```sh
curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-6.0.0-x86_64.rpm
sudo rpm -vi filebeat-6.0.0-x86_64.rpm
```
 
### Update Beats Input Plug to send logs to `Logstash`
```sh
/usr/share/logstash/bin/logstash-plugin update logstash-input-beats
```
For rpm based installation, you’ll find the configuration file at `/etc/filebeat/filebeat.yml`. If needed disable the `output.elastisearch` setting.
```sh
filebeat.prospectors:
- input_type: log
  enabled: true
  paths:
    - /var/log/httpd/access_log
    - /var/log/httpd/error_log
output.logstash:
  hosts: ["127.0.0.1:5044"]
```

# Create Logstash Configuration file
Be mindful of the hosts URL along with the port. By default Logstash _attempts_ to connect to elasticsearch over ports `9200/9300`. But AWS managed Elasticsearch services runs on protocol/port `HTTPS/443`
```sh
cat > /etc/logstash/conf.d/logstash-apache.conf << "EOF"
input {
  beats {
    # The port to listen on for filebeat connections.
    port => 5044
    # The IP address to listen for filebeat connections.
    host => "127.0.0.1"
  }
}
output {
  elasticsearch {
    hosts => "https://search-es-on-aws-c3qarpcewwgjndhddv4k7kyrzq.ap-south-1.es.amazonaws.com:443"
    manage_template => false
  }
}
EOF
```


### Confirm logstash configuration
The `--config.test_and_exit` option parses your configuration file and reports any errors
```sh
/usr/share/logstash/bin/logstash --path.settings=/etc/logstash -f /etc/logstash/conf.d/logstash-apache.conf --config.test_and_exit &
```
### Start Logstash to collect logs from `Filebeat`
If the configuration file passes the configuration test, start Logstash with the following command,
```sh
/usr/share/logstash/bin/logstash -f /etc/logstash/conf.d/logstash-apache.conf  --path.settings=/etc/logstash --config.reload.automatic &
```
## Start sending logs to Elastisearch
### Start `Logstash` Service
```sh
systemctl start logstash
# To check status
systemctl status logstash
```

### Start `Filebeat` Service
```sh
systemctl start filebeat
```

### Logstash `logs`
```sh
tail -f /var/log/logstash/logstash-plain.log
```

**PLEASE NOTE**: You may have to give permissions to `logstash` user to the log files you want to push to elasticsearch