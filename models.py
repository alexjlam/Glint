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

    def __unicode__(self):
        return self.image_name

class Site(models.Model):
    user = models.ForeignKey(MyUser)
    site_name = models.CharField(max_length=50)
    site_RC_file = models.FileField(upload_to=get_file_path)
    site_password = models.CharField(max_length=50, editable=False)

    def __unicode__(self):
        return self.site_name

class Deployed_Image(models.Model):
    user = models.ForeignKey(MyUser)
    image = models.ForeignKey(Image)
    image_identity = models.CharField(max_length=500)
    site = models.ForeignKey(Site)
    deployed_image_name = models.CharField(max_length=500)

    def __unicode__(self):
        return self.deployed_image_name

# not used
class Instance(models.Model):
    user = models.ForeignKey(MyUser)
    instance_name = models.CharField(max_length=50)
    instance_identity = models.CharField(max_length=100)
    deployed_image = models.ForeignKey(Deployed_Image)

    def __unicode__(self):
        return self.instance_name

# not currently being used now
# currently generating a new token for each time we create/delete an image
class Token(models.Model):
    user = models.ForeignKey(MyUser)
    site = models.ForeignKey(Site)
    token = models.CharField(max_length=5000)
    name = models.CharField(max_length=50)
    expiry_date = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

