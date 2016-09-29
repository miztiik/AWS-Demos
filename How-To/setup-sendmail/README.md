# Install Sendmail & Configuration file

Lets install the `sendmail` packages its configuration file `sendmail-cf`. 

```sh
yum -y install sendmail sendmail-cf m4 -y
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
Avoid editing the sendmail.cf file directly. To make configuration changes to Sendmail, edit the `/etc/mail/sendmail.mc` file, back up the original `/etc/mail/sendmail.cf` file, and use the following alternatives to generate a new configuration file

The package `m4` macro processor assists in making changes to the sendmail config files

```sh
make all -C /etc/mail/
or 
yum -y install m4
```

Various Sendmail configuration files are installed in the /etc/mail/ directory including:
 -`access` — Specifies which systems can use Sendmail for outbound email.
 -`domaintable` — Specifies domain name mapping.
 -`local-host-names` — Specifies aliases for the host.
 -`mailertable` — Specifies instructions that override routing for particular domains.
 -`virtusertable` — Specifies a domain-specific form of aliasing, allowing multiple virtual domains to be hosted on one machine.

Several of the configuration files in `/etc/mail/`, such as access, domaintable, mailertable and virtusertable, must actually store their information in database files before Sendmail can use any configuration changes. 

For example, to have all emails addressed to the example.com domain delivered to bob@other-example.com, add the following line to the virtusertable file:
```sh
@example.com bob@other-example.com
```
To finalize the change, the `virtusertable.db` file must be updated:
```sh
~]# makemap hash /etc/mail/virtusertable < /etc/mail/virtusertable
```
Sendmail will create an updated `virtusertable.db` file containing the new configuration.


## Testsing sendmail
```sh
echo "Mail from server:`uname -n`" | sendmail -v user@example.com
```
_or_ a more detailed example
```sh
[server]$ /usr/sbin/sendmail youremail@example.com
To: differentemail@example.com
From: ayouremail@example.com
Subject: Test Send Mail
Hello World
control + d (this key combination will finish the email.)
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
### Force Mail Queue Processing in the Mail Queue
```sh
/usr/lib/sendmail -q -v 
```
