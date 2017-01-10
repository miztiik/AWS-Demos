# SECURING VIRTUAL PRIVATE NETWORKS (VPNS) USING IPSec

###### Ref [1] - https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/7/html/Security_Guide/sec-Securing_Virtual_Private_Networks.html
###### Ref [2] - https://libreswan.org/wiki/Host_to_host_VPN_with_PSK
###### Ref [3] - https://aws.amazon.com/articles/5472675506466066


In Red Hat Enterprise Linux 7, a Virtual Private Network (VPN) can be configured using the IPsec tunneling protocol which is supported by the `Libreswan` application. `Libreswan` is a fork of the `Openswan` application and examples in documentation should be interchangeable.

IPsec can be implemented using a host-to-host (one computer workstation to another) or network-to-network (one LAN/WAN to another).

There are three commonly used methods for authentication of endpoints:
 - **Pre-Shared Keys (PSK)** is the simplest authentication method. PSK's should consist of random characters and have a length of at least 20 characters. Due to the dangers of non-random and short PSKs, this method is not available when the system is running in FIPS mode.
 - Raw **RSA keys** are commonly used for static host-to-host or subnet-to-subnet IPsec configurations. The hosts are manually configured with each other's public RSA key. This method does not scale well when dozens or more hosts all need to setup IPsec tunnels to each other.
 - **X.509 certificates** are commonly used for large scale deployments where there are many hosts that need to connect to a common IPsec gateway. A central certificate authority (CA) is used to sign RSA certificates for hosts or users. This central CA is responsible for relaying trust, including the revocations of individual hosts or users.

The IPsec implementation in Red Hat Enterprise Linux uses Internet Key Exchange (IKE) Protocol, an IPsec connection uses the _pre-shared key_ method of IPsec node authentication. In a pre-shared key IPsec connection, both hosts must use the same key in order to move to the second phase of the IPsec connection. 

Libreswan uses the `Network security services` (NSS) cryptographic library, which is required for `Federal Information Processing Standard` (FIPS) security compliance.


**IMPORTANT** - _`IPsec`, implemented by Libreswan, is the only VPN technology recommend for use in Red Hat Enterprise Linux 7. Do not use any other VPN technology without understanding the risks of doing so._

## IPsec VPN Using Libreswan
```sh
yum -y install libreswan
```
To check that `Libreswan` is installed,
```sh
yum info libreswan
```
Checking the version,
```sh
#/usr/libexec/ipsec/pluto --version
Libreswan 3.15 XFRM(netkey) KLIPS NSS DNSSEC FIPS_CHECK LABELED_IPSEC LIBCAP_NG LINUX_AUDIT XAUTH_PAM NETWORKMANAGER CURL(non-NSS) LDAP(non-NSS)
```

### Clean up installation defaults:
After a new installation of Libreswan the `NSS database` should be initialized as part of the install process. However, should you need to start a new database, first remove the old database as follows:
```sh
rm -rf /etc/ipsec.d/*.db
```

## Initialize the NSS Database
```sh
ipsec initnss
```
If you do not want to use a password for NSS, just press `Enter` twice when prompted for the password. If you do enter a password then you will have to re-enter it every time `Libreswan` is started, such as every time the system is booted.

### Start IPSec
```sh
systemctl start ipsec
```
#### Enable ipsec at boot
Ensure that `Libreswan` will start when the system starts,
```sh
systemctl enable ipsec
```

## Enable firewall rules
Libreswan requires the firewall to allow the following packets:
 - UDP port 500 for the Internet Key Exchange (IKE) protocol
 - UDP port 4500 for IKE NAT-Traversal
 - Protocol 50 for Encapsulated Security Payload (ESP) IPsec packets
 - Protocol 51 for Authenticated Header (AH) IPsec packets (uncommon)

##### Turning on Packet Forwarding
###### Ref - https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Load_Balancer_Administration/s1-lvs-forwarding-VSA.html

To check if IP forwarding is turned on, issue the following command as root:
`/sbin/sysctl net.ipv4.ip_forward`

If the above command returns a `1`, then IP forwarding is enabled. If it returns a `0`, then you can turn it on manually using the following command:

Add the following lines in `/etc/sysctl.conf`
```sh
# IPSec 
net.ipv4.ip_forward = 1

net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0

net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.send_redirects = 0

net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.conf.default.log_martians = 0

net.ipv4.conf.default.rp_filter = 0
net.ipv4.conf.all.rp_filter = 0
net.ipv4.conf.eth0.rp_filter = 0
net.ipv4.conf.ip_vti0.rp_filter = 0

```
Type this as root `sysctl -p` or The changes take effect when you reboot the system .

## Host-To-Host VPN Using Libreswan
Run the following commands as root on both of the hosts (“left” and “right”) to create new raw RSA key pairs:

```sh
ipsec newhostkey --configdir /etc/ipsec.d --output /etc/ipsec.d/naccrd.com.secrets
```
Now that we have generated RSA key pair using the NSS database,  To view the keys,

```sh
ipsec showhostkey --left
```

### View the public key
Run the following command as root on either of the hosts. For example, to view the public key on the “left” host:
```sh
ipsec showhostkey --left
```

## Configure IpSec
There are two steps to it, 
 - The lines `leftrsasigkey=` and `rightrsasigkey=` from the above view command, are to be added to a custom configuration file placed in the `/etc/ipsec.d/` directory. 
 - Enable `Libreswan` to read the custom configurations files, Edit the main configuration file, `/etc/ipsec.conf`, uncomment the line `include /etc/ipsec.d/*.conf`

#### Step 1 : Allow IPSec to read and load configuration modules
```sh
 include /etc/ipsec.d/*.conf
```

Confirm the same by running this command,
```sh
more /etc/ipsec.conf | grep -v "#" | grep -i include
```
```
config setup
        protostack=netkey
        logfile=/var/log/pluto.log
        dumpdir=/var/run/pluto/
        virtual_private=%v4:10.0.0.0/8,%v4:192.168.0.0/16,%v4:172.16.0.0/12,%v4:25.0.0.0/8,%v4:100.64.0.0/10,%v6:fd00::/8,%v6:fe80::/10
        nat_traversal=yes

include /etc/ipsec.d/*.conf
```

#### Step 2 : Create Configuration modules
Create a file with a suitable name in the following format, `/etc/ipsec.d/<my_host-to-host>.conf`
```sh
touch /etc/ipsec.d/onprem-to-aws.conf
```
Lets add contents to the file,
```sh
cat > /etc/ipsec.d/onprem-to-aws.conf << "EOF"
conn mytunnel
    leftid=@us6q
    left=10.188.60.201
    leftrsasigkey=0sAQOXIdVCvLT8SsP/unqb1eKVKBec3fbuJvcuguGE8KD54/YNTclweejkyJXBE9STGr+ASZDHDOmScKVF0jU7vPSdyB8V+HgyiUnz71Sph65MfNvU7wUWdDLsrZ6MthkJwOKnIkegzb7BYydoEcGgNJONGntXbovlxcHbnC/DIeyCeOIiAISdl3pMzjYalg2R+//0hVBYz/u2/r5wfys6bsovCy2xhVrCyrCufBIuiUtr66xQ07EFEbdGwFYAxjychNFX4bclZKumLUv/+TSoel4GLoDbaF30o3F8vst7oH6VFyumnsh6gB+Muy6sDzvT7oj9uJhjSxGR63wt/COO4a0DPK/i4N/M+72z2gqGfa/9rKp7I8zB67HPDQWRa+syFOPWG3rvYCM3x80Dz25YivoT6wBYDmrxpOMig5gy73W/x7cuXbyFz0LoCZHIKhh0NH6Gilb/M/S2s+WuRo9QZZ3TfKJBwD+Fai10/WaKdtXXGBlxAuiN0ticgYVLMRYCIZN0cjWgla27JfOV49YbmUF0Mrs=
    rightid=@us6p
    right=10.188.50.255
    rightrsasigkey=0sAQO4BhWccAeVzwyKhd4DLi43Qd8jbzeVXbk0U5I7u+2Hlnt6B5f+tRQoRI9btZOWoupGRZtZVmeqbQaqaVNhsotzIw+6CtA1eRPlWtc2wGXIfwTF6ORze0/AvX2PFIPjYP/77IEt1YWTdxOZN0Zj4nOSF0l6La3EvjFYNCu3c44UI4YzgIxOtymillZ/RZUnLcmDbpQcXqOplgLCe5FObIltieepY5A+z/zIXFo+E+epm53g6Nr636KREM5xFmXc0S3HPi5Y6Y3BAweA0omAHgH2a5lrQNkZpm5GR/6SIWkrlvrJ8VxsvUcyKpZCGWskKEU+Y5mkGZAtK5Ib99qMWZjd4DkC9S40slrYl7MoEKg4QrDY+lbHAelcUd1bFJDepbslyggCNouoO+961ebiwMMJ4uHadPghcninxsAu/vSAVtr4oGWv1S5Pt65ocmXrcSAA3dRWWyhDOuDga7atWWJfwHxJyUaOWHJzDUjTHvDOgtPzFPn8y6hdUnvYomcpmqxn1r4GYYLZ+QgefvjFLqthujeMvraw57cp2MlDwzr0qlWXUmn01QzOUDt5blbp6am/psoKxc1c4infAFqNw4W1p0U=
    authby=rsasig
    # load and initiate automatically
    auto=start
EOF
```

**Note:** _Ensure the leftrsasigkey value is obtained from the “left” host and the rightrsasigkey value is obtained from the “right” host._

### Restart ipsec to ensure it reads the new configuration

##### Ensure ipsec is started
```sh
ipsec setup start
systemctl restart ipsec
```

Load the secrets:
```sh
ipsec auto --rereadsecrets
```
### Check the configurations
```sh
ipsec addconn --checkconfig
```
The return code for that should be 0, otherwise the scripts might refuse to (re)start ipsec.

### Verifying the configurations
```sh

~]# ipsec verify
Verifying installed system and configuration files

Version check and ipsec on-path                         [OK]
Libreswan 3.15 (netkey) on 3.10.0-514.2.2.el7.x86_64
Checking for IPsec support in kernel                    [OK]
 NETKEY: Testing XFRM related proc values
         ICMP default/send_redirects                    [OK]
         ICMP default/accept_redirects                  [OK]
         XFRM larval drop                               [OK]
Pluto ipsec.conf syntax                                 [OK]
Hardware random device                                  [N/A]
Two or more interfaces found, checking IP forwarding    [OK]
Checking rp_filter                                      [OK]
Checking that pluto is running                          [OK]
 Pluto listening for IKE on udp 500                     [OK]
 Pluto listening for IKE/NAT-T on udp 4500              [OK]
 Pluto ipsec.secret syntax                              [OK]
Checking 'ip' command                                   [OK]
Checking 'iptables' command                             [OK]
Checking 'prelink' command does not interfere with FIPSChecking for obsolete ipsec.conf options                 [OK]
Opportunistic Encryption                                [DISABLED]
```

### Load the IPsec tunnel
```sh
ipsec auto --add mytunnel --verbose
```
If you want verbose output, add `--verbose` at the end of the command

#### To bring up the tunnel on the left or the right side,
```sh
ipsec auto --up mytunnel
```

## Check the IPSec Tunnel
In `/var/log/secure` look for and established messages like "IPsec SA established"
```sh
~]# more /var/log/secure | grep -i "IPsec SA established"
Oct 27 07:23:05 us6q pluto[8764]: "mytunnel" #2: STATE_QUICK_I2: sent QI2, IPsec SA established tunnel mode {ESP=>0x38c53504 <0xbcb3fdf5 xfrm=AES_128-HMAC_SHA1 NATOA=none NATD=none DPD=passive}
Oct 27 07:23:09 us6q pluto[8764]: "mytunnel" #4: STATE_QUICK_R2: IPsec SA established tunnel mode {ESP=>0xe952ea2e <0x3c3b18ab xfrm=AES_128-HMAC_SHA1 NATOA=none NATD=none DPD=passive}
Oct 27 07:24:10 us6q pluto[8764]: "mytunnel" #6: STATE_QUICK_R2: IPsec SA established tunnel mode {ESP=>0x32d940e4 <0xd8ea76c7 xfrm=AES_128-HMAC_SHA1 NATOA=none NATD=none DPD=passive}
```

_Another way to check_, from kernel policies:
```sh
~]# ip xfrm policy
src 10.188.60.201/32 dst 10.188.50.255/32
        dir out priority 2080 ptype main
        tmpl src 10.188.60.201 dst 10.188.50.255
                proto esp reqid 16401 mode tunnel
src 10.188.50.255/32 dst 10.188.60.201/32
        dir fwd priority 2080 ptype main
        tmpl src 10.188.50.255 dst 10.188.60.201
                proto esp reqid 16401 mode tunnel
src 10.188.50.255/32 dst 10.188.60.201/32
        dir in priority 2080 ptype main
        tmpl src 10.188.50.255 dst 10.188.60.201
                proto esp reqid 16401 mode tunnel
src ::/0 dst ::/0 proto ipv6-icmp type 135
```
You can also collect `tcpdump` and review the logs:
```sh
tcpdump -n -i eth0 esp or udp port 500 or udp port 4500
```
