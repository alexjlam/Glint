from django.contrib import admin
from django.contrib.auth.models import User
from openstack.models import MyUser, Image, Site, Deployed_Image, Instance
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm

class ImageInline(admin.TabularInline):
    model = Image
    extra = 1

class SiteInline(admin.TabularInline):
    model = Site
    extra = 1

class Deployed_ImageInline(admin.TabularInline):
    model = Deployed_Image
    extra = 1

class MyUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = MyUser

class MyUserAdmin(UserAdmin):
    inlines = [ImageInline, SiteInline, Deployed_ImageInline]
    form = MyUserChangeForm
    fieldsets = UserAdmin.fieldsets

admin.site.register(MyUser, MyUserAdmin)
admin.site.register(Image)
admin.site.register(Site)
admin.site.register(Deployed_Image)
