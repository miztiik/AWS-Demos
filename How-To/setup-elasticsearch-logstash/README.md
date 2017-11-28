# AWS ElasticSearch with Logstash(in EC2)

You can have your own VPC and run Elasticsearch and Logstash inside the VPC, but we are going to use a public version.
Lets setup up the EC2 Logstash

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
```

#### Install `logstash-beats-plugin`
```sh
/usr/share/logstash/bin/logstash-plugin install logstash-input-beats
```

# Create Logstash Configuration file
Be mindful of the hosts URL along with the port. By default Logstash _attempts_ to connect to elasticsearch over ports `9200/9300`. But AWS managed Elasticsearch services runs on protocol/port `HTTPS/443`
```sh
cat > /etc/logstash/conf.d/logstash-syslog.conf << "EOF"

input {
  file {
    type => syslog
    path => [ "/var/log/messages", "/var/log/*.log" ]
  }
}

output {
  stdout {
    codec => rubydebug
  }
  elasticsearch {
    hosts => ["https://search-xxx-oxcuuxxx.us-east-1.es.amazonaws.com:443"]
  }
}
EOF

cat > /etc/logstash/conf.d/logstash-apache.conf << "EOF"
input {
  beats {
    port => 5044
  }
}
output {
  elasticsearch {
    hosts => "https://search-es-on-aws-c3qarpcewwgjndhddv4k7kyrzq.ap-south-1.es.amazonaws.com:443"
    manage_template => false
    index => "%{[@metadata][beat]}-%{+YYYY.MM.dd}"
    document_type => "%{[@metadata][type]}"
  }
}
EOF
```

### Start Logstash Service
```sh
systemctl start logstash
# To check status
systemctl status logstash
```

### Confirm logstash configuration
The `--config.test_and_exit` option parses your configuration file and reports any errors
```sh
/usr/share/logstash/bin/logstash --path.settings=/etc/logstash -f /etc/logstash/conf.d/logstash-syslog.conf --config.test_and_exit
```

### Start sending logs to Elastisearch
If the configuration file passes the configuration test, start Logstash with the following command,
```sh
/usr/share/logstash/bin/logstash -f /etc/logstash/conf.d/logstash-syslog.conf  --path.settings=/etc/logstash --config.reload.automatic
```

### Logstash `logs`
```sh
tail -f /var/log/logstash/logstash-plain.log
```

**PLEASE NOTE**: You may have to give permissions to `logstash` user to the log files you want to push to elasticsearch

# Install `Filebeat`
```sh
curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-6.0.0-x86_64.rpm
sudo rpm -vi filebeat-6.0.0-x86_64.rpm
```
 
### Update Beats Input Plug to send logs to `Logstash`
```sh
/usr/share/logstash/bin/logstash-plugin update logstash-input-beats
```
For rpm based installation, you’ll find the configuration file at `/etc/filebeat/filebeat.yml`
```sh
filebeat.prospectors:
- type: log
  enabled: true
  paths:
    - /var/log/httpd/*.log  
    - /var/log/messages.log
    
```

### Apache2 module
The `apache2` module parses access and error logs created by the Apache HTTP server.

When you run the module, it performs a few tasks under the hood:

- Sets the default paths to the log files (but don’t worry, you can override the defaults)
- Makes sure each multiline log event gets sent as a single event
- Uses ingest node to parse and process the log lines, shaping the data into a structure suitable for visualizing in Kibana
- Deploys dashboards for visualizing the log data

```sh
filebeat modules enable apache2
```

List of enabled and disabled modules,
```sh
filebeat modules list
```


### Start `Filebeat`
```sh
systemctl start filebeat
```