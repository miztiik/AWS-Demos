
#!/bin/bash

# Install epel
curl -O http://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
rpm -ivh epel-release-latest-7.noarch.rpm

# Install httpd server
yum -y install httpd

# Enable the httpd server to start at boot
systemctl enable httpd


# Create our index file
cat > /var/www/html/index.html <<- "EOF"
<html>
<br /><br />
<pre>                         

           __  __ _                 _                        _   _             
     /\   |  \/  (_)     /\        | |                      | | (_)            
    /  \  | \  / |_     /  \  _   _| |_ ___  _ __ ___   __ _| |_ _  ___  _ __  
   / /\ \ | |\/| | |   / /\ \| | | | __/ _ \| '_ ` _ \ / _` | __| |/ _ \| '_ \ 
  / ____ \| |  | | |  / ____ \ |_| | || (_) | | | | | | (_| | |_| | (_) | | | |
 /_/    \_\_|  |_|_| /_/    \_\__,_|\__\___/|_| |_| |_|\__,_|\__|_|\___/|_| |_|

</pre>
<br />
</html>
EOF


# Re-Start the service
systemctl restart httpd


## Edit the MOTD to display something nice
>>/etc/motd
cat > /etc/motd <<- "EOF"

           __  __ _                 _                        _   _             
     /\   |  \/  (_)     /\        | |                      | | (_)            
    /  \  | \  / |_     /  \  _   _| |_ ___  _ __ ___   __ _| |_ _  ___  _ __  
   / /\ \ | |\/| | |   / /\ \| | | | __/ _ \| '_ ` _ \ / _` | __| |/ _ \| '_ \ 
  / ____ \| |  | | |  / ____ \ |_| | || (_) | | | | | | (_| | |_| | (_) | | | |
 /_/    \_\_|  |_|_| /_/    \_\__,_|\__\___/|_| |_| |_|\__,_|\__|_|\___/|_| |_|

EOF


# Install the clam Antivirus
sudo yum --enablerepo=epel install -y clamav

# Disable epel
yum-config-manager --disable epel