For future co-op students to continue work on Glint

When you are ready to start working on Glint you will need to have the following installed:

Django 1.6
https://docs.djangoproject.com/en/1.6/topics/install/
(I also recommend going through the tutorial for Django as well)
python 2.7
python glanceclient
python keystoneclient
python boto
EC2 CLI and AMI tools and Java
http://docs.aws.amazon.com/AWSEC2/latest/CommandLineReference/set-up-ec2-cli-linux.html
http://docs.aws.amazon.com/AWSEC2/latest/CommandLineReference/set-up-ami-tools.html

Once those are installed, follow the instructions below to set up the project:

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
        'vmdist', (in INSTALLED_APPS)
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

note: when you are using the EC2 clouds, you will need to source ec2-env.sh before running the server so the program can find the AMI and CLI tool homes

stuff to work on:
launching AMIs on EC2 fails on instance status check
upgrading to Django 1.7 architecture when it comes out
deleting images and site files from the server will not update the model, and deleting an image via admin page will not deletethe file from the server
bundle_image(), create_ami() in ec2_utils and convert_image() in openstack_utils use subprocess
for deploying images to EC2, if the account number, certificate, or private key is wrong, it will not know if they are good until you try to launch the AMI
