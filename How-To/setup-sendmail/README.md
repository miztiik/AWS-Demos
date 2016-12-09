# Install Sendmail & Configuration file

Lets install the `sendmail` packages its configuration file `sendmail-cf`. 

```sh
yum -y install sendmail sendmail-cf m4
```
### Ensure sendmail is started by default
```sh
systemctl enable sendmail.service
```
To confirm if sendmail is running,
```sh
systemctl list-units --type service | grep sendmail
or
systemctl status sendmail
or
ps auxw| grep [s]endmail
```


## Set the MTA to `sendmail`
Red Hat Enterprise Linux offers two primary MTAs: Postfix and Sendmail. Postfix is configured as the default MTA, although it is easy to switch the default MTA to Sendmail. To switch the default MTA to Sendmail, you can either uninstall Postfix or use the following command to switch to Sendmail:
```sh
alternatives --config mta
```

The output of the above will be like,
```sh
[root@server01 mail]# alternatives --config mta

There are 2 programs which provide 'mta'.

  Selection    Command
-----------------------------------------------
   1           /usr/sbin/sendmail.postfix
*+ 2           /usr/sbin/sendmail.sendmail

Enter to keep the current selection[+], or type selection number: 2
[root@server01 mail]#

or

[root@server01 mail]# alternatives --set mta /usr/sbin/sendmail.sendmail
```
### Disable postfix
```sh
systemctl disable postfix
systemctl status postfix

or
systemctl list-units --type service --all | grep postfix
```

## Configuring Sendmail
By default sendmail server allows to connect to local host only. So we should edit the `/etc/mail/sendmail.mc` file to allow connect to other hosts. The sendmail daemon is configured from a directory of files in `/etc/mail` and a directory of configuration files in `/usr/share/sendmail-cf`. 

There are two basic configuration files:
 - `sendmail.cf` - The main sendmail configuration file.
 - `sendmail.mc` - A macro that's easier to edit, which can be used to generate a new sendmail.cf file.

Other Sendmail configuration files are installed in the `/etc/mail/` directory including:
 - `access` : Specifies which systems can use Sendmail for outbound email.
 - `domaintable` : Specifies domain name mapping.
 - `local-host-names` : Specifies aliases for the host.
 - `mailertable` : Specifies instructions that override routing for particular domains.
 - `virtusertable` : Specifies a domain-specific form of aliasing, allowing multiple virtual domains to be hosted on one machine.

Avoid editing the sendmail.cf file directly. To make configuration changes to Sendmail, edit the `/etc/mail/sendmail.mc` file, back up the original `/etc/mail/sendmail.cf` file, and use the following alternatives to generate a new configuration file

The package `m4` macro processor assists in making changes to the sendmail config files

```sh
make all -C /etc/mail/
or 
yum -y install m4
```

Several of the configuration files in `/etc/mail/`, such as `access`, `domaintable`, `mailertable` and `virtusertable`, must actually store their information in database files before Sendmail can use any configuration changes.

#### Disable loop-back address
By default, the following line limits sendmail access to local host only `sendmail.mc` You can allow other computers to use your sendmail server by commenting out this line. 

In the `sendmail.mc` file , lines that begin with dnl, which stands for delete to new line, are considered comments. Some lines end with dnl, but lines ending in dnl are not comments.

The following line should be commented to ( with dnl keyword followed by # sign)
```sh
DAEMON_OPTIONS(`Port=smtp,Addr=127.0.0.1, Name=MTA')dnl
```
to
```sh
dnl # DAEMON_OPTIONS(`Port=smtp,Addr=127.0.0.1, Name=MTA')dnl
```
Now generate new `sendmail.cf` file by using `m4` command as shown here,
```sh
m4 /etc/mail/sendmail.mc > /etc/mail.sendmail.cf && \
systemctl restart sendmail
```

#### Updating `mailertable`
Edit the `/etc/mail/mailertable` file with your domains. For help, refer [here](http://www.sendmail.com/sm/open_source/docs/m4/mailertables.html). 
```sh
my.domain		esmtp:host.my.domain
```
After saving your edits, update the db with the `makemap hash` command
```sh
makemap hash /etc/mail/mailertable < /etc/mail/mailertable && \
systemctl restart sendmail
```

_**NOTE : YOUR MAIL RELAY SHOULD BE ABLE TO RESOLVE & REACH THE DOMAINS LISTED IN MAILERTABLE. ENSURE YOUR DNS & NETWORKS ARE IN ORDER BEFORE TESTING**_

#### Updating `virtualusertable`
For example, to have all emails addressed to the _example.com_ domain delivered to _bob@other-example.com_, add the following line to the virtusertable file:

```sh
@example.com bob@other-example.com
```
To finalize the change, the `virtusertable.db` file must be updated:
```sh
makemap hash /etc/mail/virtusertable < /etc/mail/virtusertable && \
systemctl restart sendmail
```
Sendmail will create an updated `virtusertable.db` file containing the new configuration. When Sendmail is started or restarted a new `sendmail.cf` file is automatically generated if `sendmail.mc` has been modified.


## Testing sendmail
```sh
echo "Mail from server:`uname -n` on date: `date`" | sendmail -v user@example.com
```
_or_ a more detailed example
```sh
[server01]$ /usr/sbin/sendmail youremail@example.com
To: differentemail@example.com
From: ayouremail@example.com
Subject: Test Send Mail
Hello World
control + d (this key combination will finish the email.)
```
_or_ **eMailing a report contents:**
```sh
sendmail -s 'Subject-Here' you@email.com < "input.file"
```

## List messages in sendmail queue
```sh
sendmail -bp
```
shows the following output,
```sh
[root@server01 mqueue]# sendmail -bp
                /var/spool/mqueue (2 requests)
-----Q-ID----- --Size-- -----Q-Time----- ------------Sender/Recipient-----------
u8T9idh4006507       27 Thu Sep 29 05:44 <user@example.com>
                 (Deferred: Connection timed out with mailer.domain)
                                         <differentemail@example.com>
u8T9dlP7006496       62 Thu Sep 29 05:39 <user@example.com>
                 (Deferred: Connection timed out with mailer.domain)
                                         <differentemail@example.com>
                Total requests: 2
[root@server01 mqueue]#
```
If the queue was empty you would simply get this:
```sh
/var/spool/mqueue is empty
                Total requests: 0
```
_You can also check in `/var/log/maillog` for mail log messages_
### Force Mail Queue Processing in the Mail Queue
```sh
/usr/lib/sendmail -q -v 
```

### Automating the sendmail config updates
```sh
cat > /etc/mail/update.sh << EOF
#!/usr/bin/bash
set -x

cd /etc/mail

/usr/sbin/sendmail -v -bi

# Update the map files
/usr/sbin/makemap hash access < access
/usr/sbin/makemap hash virtusertable < virtusertable
/usr/sbin/makemap hash mailertable < mailertable

# cd /etc/mail/auth
# /usr/sbin/makemap hash client-info < client-info
# /usr/sbin/makemap hash auth-info < auth-info

# Kill the current sendmail session
if [[ -f /var/run/sendmail.pid ]]
then
    /bin/kill -HUP `/usr/bin/head -1 /var/run/sendmail.pid`
fi
# Restart sendmail after all updates
systemctl restart sendmail
systemctl status sendmail
EOF
```
Set the permissions for execution,
```sh
chmod 700 /etc/mail/update.sh
```
