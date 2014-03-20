from django.db import models
from django.contrib.auth.models import User, AbstractUser
import os

def get_file_path(instance, filename):
    return os.path.join("%s" % instance.user, "%s" % filename)

class MyUser(AbstractUser):
    data = models.CharField(max_length=100)

class Image(models.Model):
    user = models.ForeignKey(MyUser)
    image_file = models.FileField(upload_to=get_file_path, blank=True)
    image_addr = models.CharField(max_length=500, blank=True)
    image_name = models.CharField(max_length=500)
    bundled = models.BooleanField(default=False)

    def __unicode__(self):
        return self.image_name

class Site(models.Model):
    user = models.ForeignKey(MyUser)
    site_name = models.CharField(max_length=50)
    site_RC_file = models.FileField(upload_to=get_file_path, blank=True)
    site_password = models.CharField(max_length=50, editable=False, blank=True)
    token = models.CharField(max_length=5000, blank=True)
    endpoint = models.CharField(max_length=50, blank=True)
    site_type = models.CharField(max_length=50)

    def __unicode__(self):
        return self.site_name

class EC2_Cred(models.Model):
    user = models.OneToOneField(MyUser)
    account = models.CharField(max_length=50)
    access_key = models.CharField(max_length=100)
    secret_key = models.CharField(max_length=100)
    cert = models.FileField(upload_to=get_file_path, blank=True)
    private_key = models.FileField(upload_to=get_file_path, blank=True)

    def __unicode__(self):
        return self.account

class Deployed_Image(models.Model):
    user = models.ForeignKey(MyUser)
    deployed_image_name = models.CharField(max_length=500)
    image = models.ForeignKey(Image)
    site = models.ForeignKey(Site)
    image_identity = models.CharField(max_length=500)
    bucket = models.CharField(max_length=500, blank=True)

    def __unicode__(self):
        return self.deployed_image_name

