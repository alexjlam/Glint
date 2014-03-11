from django.conf.urls import patterns, url

from openstack import views

urlpatterns = patterns('',
    url(r'^$', views.home, name='home'),
    url(r'^jsonhandler/$', views.jsonhandler, name='jsonhandler'),
    url(r'^logout/$', views.logout_user, name='logout_user'),
    url(r'^images/$', views.images, name='images'),
    url(r'^sites/$', views.sites, name='sites'),
    url(r'^image_added/$', views.image_added, name='image_added'),
    url(r'^site_added/$', views.site_added, name='site_added'),
    url(r'^image_removed/$', views.image_removed, name='image_removed'),
    url(r'^site_removed/$', views.site_removed, name='site_removed'),

    # all not used
    url(r'^deploy/$', views.deploy, name='deploy'),
    url(r'^deploy/image_deployed/$', views.image_deployed, name='image_deployed'),
    url(r'^delete/$', views.delete, name='delete'),
    url(r'^delete/image_deleted/$', views.image_deleted, name='image_deleted'),
    url(r'^launch/$', views.launch, name='launch'),
    url(r'^launch/instance_launched/$', views.instance_launched, name='instance_launched'),
    url(r'^terminate/$', views.terminate, name='terminate'),
    url(r'^terminate/instance_terminated/$', views.instance_terminated, name='instance_terminated'),
    #url(r'^test/$', views.test, name='test'),
)


