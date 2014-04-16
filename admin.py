from django.contrib import admin
from django.contrib.auth.models import User
from vmdist.models import MyUser, Image, Site, EC2_Cred, Deployed_Image
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm

class ImageInline(admin.TabularInline):
    model = Image
    extra = 1

class SiteInline(admin.TabularInline):
    model = Site
    extra = 1

class EC2_CredInline(admin.TabularInline):
    model = EC2_Cred
    extra = 0

class Deployed_ImageInline(admin.TabularInline):
    model = Deployed_Image
    extra = 1

class MyUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = MyUser

class MyUserAdmin(UserAdmin):
    inlines = [ImageInline, SiteInline, EC2_CredInline, Deployed_ImageInline]
    form = MyUserChangeForm
    fieldsets = UserAdmin.fieldsets

admin.site.register(MyUser, MyUserAdmin)
admin.site.register(Image)
admin.site.register(Site)
admin.site.register(EC2_Cred)
admin.site.register(Deployed_Image)
