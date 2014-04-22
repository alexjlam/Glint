For future co-op students to continue work on Glint

When you are ready to start working on Glint you will need to have the following installed:
Django 1.6
https://docs.djangoproject.com/en/1.6/topics/install/
python 2.7
python-glanceclient
python-keystoneclient
python-boto
EC2 CLI and AMI tools and Java
http://docs.aws.amazon.com/AWSEC2/latest/CommandLineReference/set-up-ec2-cli-linux.html
http://docs.aws.amazon.com/AWSEC2/latest/CommandLineReference/set-up-ami-tools.html

Here are some helpful links for using the above tools:
Django 1.6 Tutorial
https://docs.djangoproject.com/en/1.6/intro/tutorial01/
D3 Bar Chart Tutorial
http://bost.ocks.org/mike/bar/
Managing images with Glance command line tool
http://docs.openstack.org/user-guide/content/cli_manage_images.html
Openstack Python APIs
http://www.ibm.com/developerworks/cloud/library/cl-openstack-pythonapis/index.html?ca=drs-
Amazon EC2 command line tools documentation
http://docs.aws.amazon.com/AWSEC2/latest/CommandLineReference/command-reference.html
Amazon Web Services Python Boto documentation
http://boto.readthedocs.org/en/latest/index.html
Google Compute Engine Python Client Library
https://developers.google.com/compute/docs/api/python-guide

Once everything is installed and working, follow the instructions below to set up the project:
$ django-admin.py startproject glint
$ cd glint/
edit glint/settings.py
    add:
        import os
        BASE_DIR = os.path.dirname(os.path.dirname(__file__))
        TEMPLATE_DIRS = [os.path.join(BASE_DIR, 'templates')]
    set:
        in DATABASES 'default':
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        TIME_ZONE = 'America/Vancouver'
    comment out:
        the other TEMPLATES_DIRS, not the one you added:
            TEMPLATES_DIRS = ()
        in MIDDLEWARE_CLASSES:
            'django.middleware.csrf.CsrfViewMiddleware',
    uncomment:
        in INSTALLED_APPS:
            'django.contrib.admin',
        in MIDDLEWARE_CLASSES:
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
$ python manage.py syncdb
skip creating a superuser for now
$ git clone https://github.com/alexjlam/vmdist.git
edit glint/settings.py
    add:
        AUTH_USER_MODEL = 'vmdist.MyUser'
        in INSTALLED_APPS:
            'vmdist',
edit glint/urls.py
    from django.conf.urls import patterns, include, url
    from django.contrib.auth.views import login
    from django.contrib import admin
    admin.autodiscover()
    urlpatterns = patterns('',
        url(r'^accounts/profile/', include('vmdist.urls', namespace='vmdist')),
        url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
        url(r'^admin/', include(admin.site.urls)),
    )
$ mkdir templates/
$ mv vmdist/registration/ templates/
$ mv vmdist/admin/ templates/
$ python manage.py syncdb
create superuser (administrator account for yourself)
it might ask to delete the auth | user content type, enter 'yes'
$ python manage.py runserver x.x.x.x:8000
go to x.x.x.x:8000/admin in your browser to see admin page
go to x.x.x.x:8000/accounts/login in browser to go to login page for Glint
navigate to the Help page for instructions to deploy an image to a cloud site

You can download some lightweight test images here:
http://docs.openstack.org/image-guide/content/ch_obtaining_images.html

Links to the Openstack and Amazon dashboards for the clouds:
Openstack Mouse Cloud (Victoria, BC)
https://mouse01.heprc.uvic.ca/
Openstack Dair Cloud (Edmonton, AB)
https://nova-ab.dair-atir.canarie.ca/
Openstack Alto Cloud (Ottawa, ON)
https://alto.cloud.nrc.ca/
Amazon EC2 Management Console
https://console.aws.amazon.com/ec2/v2/
Amazon S3 Management Console
https://console.aws.amazon.com/s3/

*Note: when you are using the EC2 clouds, you will need to source ec2-env.sh before running the server so the program can find the AMI and CLI tool homes

