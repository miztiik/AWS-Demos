# Configuring LVM in EC2
This walkthrough is to show how to create an "Logical Volume Manager - LVM" in Redhat Linux 7.2 running on an EC2 Instances. 

### Pre-Requisites
 - EC2 Instance running Redhat
 - Internet gateway setup for the VPC
 - Security Group updated for `Port 22` access
 - Two EBS Volumes (5GB & 2GB) attached to the instance

![LVM-Logical-Understanding](https://raw.githubusercontent.com/miztiik/AWS-Demos/master/img/hdd-pv-vg-lv-fs.jpg)

## Physical Volume - PV Creation:
Before we go ahead and create LVM, we need to create an Physical Volume on the EBS disks

There are 2 ways you can create PV

### Method 1 :
Creating partitions by using Physical Disk and creating pv by using partition
   
   `fdisk /dev/xvdb >> press n >> Prees p >> press t >> press w`

```sh
~]# fdisk /dev/xvdb
Welcome to fdisk (util-linux 2.23.2).

Changes will remain in memory only, until you decide to write them.
Be careful before using the write command.

Device does not contain a recognized partition table
Building a new DOS disklabel with disk identifier 0x271caa5a.

Command (m for help): n
Partition type:
   p   primary (0 primary, 0 extended, 4 free)
   e   extended
Select (default p): p
Partition number (1-4, default 1): 1
First sector (2048-10485759, default 2048):
Using default value 2048
Last sector, +sectors or +size{K,M,G} (2048-10485759, default 10485759):
Using default value 10485759
Partition 1 of type Linux and of size 5 GiB is set

Command (m for help): t
Selected partition 1
Hex code (type L to list all codes): 8e
Changed type of partition 'Linux' to 'Linux LVM'

Command (m for help): w
The partition table has been altered!

Calling ioctl() to re-read partition table.
Syncing disks.

~]#  fdisk -l /dev/xvdb

Disk /dev/xvdb: 5368 MB, 5368709120 bytes, 10485760 sectors
Units = sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disk label type: dos
Disk identifier: 0x271caa5a

    Device Boot      Start         End      Blocks   Id  System
/dev/xvdb1            2048    10485759     5241856   8e  Linux LVM
```
Creating the PV
```sh
~]# pvcreate /dev/xvdb1
  Physical volume "/dev/xvdb1" successfully created
~]# pvs
  PV         VG   Fmt  Attr PSize PFree
  /dev/xvdb1      lvm2 ---  5.00g 5.00g
```
### Method 2: 
Creting PV by using physical disk /dev/xvdg
```
~]# pvcreate /dev/xvdg
    Physical volume "/dev/xvdg" successfully created
```
```
~]# pvs
  PV             VG    Fmt  Attr PSize    PFree
  /dev/xvdb1           lvm2 ---     5.00g 5.00g
  /dev/xvdg            lvm2 ---     2.00g 2.00g
```
### Create Volume Group 
```
~]# vgcreate datavg /dev/xvdb1 /dev/xvdg
  Volume group "datavg" successfully created
```
```
~]# vgdisplay datavg
  --- Volume group ---
  VG Name               datavg
  System ID
  Format                lvm2
  Metadata Areas        2
  Metadata Sequence No  1
  VG Access             read/write
  VG Status             resizable
  MAX LV                0
  Cur LV                0
  Open LV               0
  Max PV                0
  Cur PV                2
  Act PV                2
  VG Size               6.99 GiB
  PE Size               4.00 MiB
  Total PE              1790
  Alloc PE / Size       0 / 0
  Free  PE / Size       1790 / 6.99 GiB
  VG UUID               jVFZYw-NXgD-JsoP-ay8u-8hr8-dgev-wMvZ0p

~]#
```
### Create Logical Volumes
```
~]# lvcreate -L 2G -n data_lv datavg
  Logical volume "data_lv" created.
```
```
~]# lvdisplay
  --- Logical volume ---
  LV Path                /dev/datavg/data_lv
  LV Name                data_lv
  VG Name                datavg
  LV UUID                iCXwBi-Pkfe-lvdK-iYqE-reMS-58nE-FyEMTp
  LV Write Access        read/write
  LV Creation host, time ip-172-31-56-77.ec2.internal, 2016-10-04 11:04:35 -0400
  LV Status              available
  # open                 0
  LV Size                2.00 GiB
  Current LE             512
  Segments               1
  Allocation             inherit
  Read ahead sectors     auto
  - currently set to     8192
  Block device           253:0
~]#
```
### Create File System
```sh
mkfs.ext4 /dev/datavg/data_lv` \
          mkdir /data` \
          mount /dev/datavg/data_lv /data` \
```
And add newly created FS entry in fstab and refresh the `fstab` to mount all the entries
```
~]# grep /data /etc/fstab
/dev/datavg/data_lv /data  ext4 defaults 0 0
~]# mount -a
~]# 
```
Check if the new filesystem had been mounted,
```
~]# df -h /data
Filesystem                  Size  Used Avail Use% Mounted on
/dev/mapper/datavg-data_lv  2.0G  6.0M  1.8G   1% /data
```
### Extend the File system `/data` size by 2GB
It is a two step activity,
 - Step 1 - Extend the Logical Volume
 - Step 2 - Resize the Filesystem to use the extended volume
```
~]# lvextend -L +2G /dev/datavg/data_lv
  Size of logical volume datavg/data_lv changed from 2.00 GiB (512 extents) to 4.00 GiB (1024 extents).
  Logical volume data_lv successfully resized.
```
```
~]# resize2fs /dev/datavg/data_lv
resize2fs 1.42.9 (28-Dec-2013)
Filesystem at /dev/datavg/data_lv is mounted on /data; on-line resizing required
old_desc_blocks = 1, new_desc_blocks = 1
The filesystem on /dev/datavg/data_lv is now 1048576 blocks long.
```
Check the size again,
```
~]# df -h /data
Filesystem                  Size  Used Avail Use% Mounted on
/dev/mapper/datavg-data_lv  3.9G  8.0M  3.7G   1% /data
```
