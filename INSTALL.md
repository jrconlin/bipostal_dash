# Installation:

## Pre-requisites:

* git

* svn

* nginx

* Python 2.6

* python-devel

* python-virtualenv

* gcc

* make

* mysql\_server

* PostFix (or any other milter compatible MTA)

## Installation:

1. $ make build

2. cp etc/bipostaldash-prod-dist.ini etc/bipostaldash.ini

   please note that you may need to modify values in this file to match your 
current install

3. bin/paster serve etc/bipostaldash.ini

This will start a server at port :8000

If you are not running an external service or are comfortable with contacting 
odd ports on the server, feel free to stop here.

4. if you are using nginx (suggested):

4.1 copy the proper bipostaldash.*.nginx.conf (based on your nginx install) 
to /etc/nginx/conf.d. 

Note that under ubuntu, conf.d files are included as 
part of server, where under redhat, they are not. Also note that for redhat,
you may need to comment out the existing server info, or manually include 
the bipostal config data in the main server config. Refer to nginx documentation
for the most optimal way to do that.

4.2 Restart nginx, ensuring that the config files pass checks.

This should set up / on the local server to point to the new bipostal dashboard.

