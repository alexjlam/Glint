from django.conf.urls import patterns, url

from vmdist import views

urlpatterns = patterns('',
    url(r'^$', views.home, name='home'),
    url(r'^jsonhandler/$', views.jsonhandler, name='jsonhandler'),
    url(r'^logout/$', views.logout_user, name='logout_user'),
    url(r'^images/$', views.images, name='images'),
    url(r'^sites/$', views.sites, name='sites'),
    url(r'^help/$', views.help, name='help'),
    url(r'^image_added/$', views.image_added, name='image_added'),
    url(r'^site_added/$', views.site_added, name='site_added'),
    url(r'^image_removed/$', views.image_removed, name='image_removed'),
    url(r'^site_removed/$', views.site_removed, name='site_removed'),
    url(r'^ec2_added/$', views.ec2_added, name='ec2_added'),
    url(r'^ec2_removed/$', views.ec2_removed, name='ec2_removed'),
    url(r'^image_bundled/$', views.image_bundled, name='image_bundled'),
    url(r'^image_converted/$', views.image_converted, name='image_converted'),
)


