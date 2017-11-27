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
```sh
yum -y install java-1.8.0-openjdk
# Confirm version of java
java - version
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
```

###### You MUST add the following config lines to your /etc/logstash/logstash.yml
**Optional: This is not mandatory!!!**
```sh
xpack.monitoring.enabled: true
xpack.monitoring.elasticsearch.url: https://search-es-on-aws-oxcuuf5uw7ksakr6s2q3ufoa3i.us-east-1.es.amazonaws.com
```

```sh
# Logstash `bin` location
# /usr/share/logstash/bin/logstash -t -f logstash-syslog.conf
```


### Start Logstash Service
```sh
systemctl start logstash
# To check status
systemctl status logstash
```


### Confirm logstash configuration
```sh
/usr/share/logstash/bin/logstash -t --path.settings=/etc/logstash -f /etc/logstash/conf.d/logstash-syslog.conf
```

### Start sending logs to Elastisearch
```sh
/usr/share/logstash/bin/logstash -f /etc/logstash/conf.d/logstash-syslog.conf  --path.settings=/etc/logstash
```

### Logstash `logs`
```sh
tail -f /var/log/logstash/logstash-plain.log
```

**PLEASE NOTE**: You may have to give permissions to `logstash` user to the log files you want to push to elasticsearch