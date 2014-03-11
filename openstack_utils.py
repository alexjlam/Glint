#!/usr/bin/env python

import subprocess, requests, json, re
from keystoneclient.v2_0 import client as keyclient
from keystoneclient.apiclient.exceptions import Unauthorized
from glanceclient.v1 import client as glclient
from novaclient.v1_1 import client as nvclient

def export_RC_file(site_file):
    """
    extracts information from site RC file
    """
    RC_dict = {}
    for line in open(site_file, 'r'):
        if re.search('export OS_AUTH_URL=(.+)', line):
            RC_dict['OS_AUTH_URL'] = re.search('export OS_AUTH_URL=(.*)', line).group(1).strip()
        if re.search('export OS_TENANT_ID=(.+)', line):
            RC_dict['OS_TENANT_ID'] = re.search('export OS_TENANT_ID=(.*)', line).group(1).strip()
        if re.search('export OS_TENANT_NAME="?([^"]+)"?', line):
            RC_dict['OS_TENANT_NAME'] = re.search('export OS_TENANT_NAME="?([^"]+)"?', line).group(1).strip()
        if re.search('export OS_USERNAME="?([^"]+)"?', line):
            RC_dict['OS_USERNAME'] = re.search('export OS_USERNAME="?([^"]+)"?', line).group(1).strip()
    return RC_dict

def get_token_and_ep(RC_dict):
    """
    creates a new token using the keystoneclient and gets the endpoint
    """
    keystone = keyclient.Client(username=RC_dict['OS_USERNAME'], password=RC_dict['OS_PASSWORD'], tenant_name=RC_dict['OS_TENANT_NAME'], auth_url=RC_dict['OS_AUTH_URL'])
    # to return the whole token dictionary
    # return keystone.auth_ref
    token = keystone.auth_token
    endpoint = keystone.service_catalog.url_for(service_type='image',endpoint_type='publicURL')
    return token, endpoint

def create_image(image, site, ids, errors, i):
    """
    create an image on the site using the glanceclient
    """    
    name = image.image_name
    site_file = str(site.site_RC_file)

    try:
        # exports info from RC file from the site and gets a token and endpoint
        RC_dict = export_RC_file(site_file)
        RC_dict['OS_PASSWORD'] = str(site.site_password)
        token, endpoint = get_token_and_ep(RC_dict)

        # uses the token and endpoint to get a glanceclient
        glance = glclient.Client(endpoint=endpoint, token=token)

        # create an image with a file
        if image.image_file != "":
            image_file = str(image.image_file)
            with open(image_file) as fimage:
                image = glance.images.create(name=name, disk_format="qcow2", container_format="bare", data=fimage)
        # creates an image with a website address
        else:
            image = glance.images.create(name=name, disk_format="qcow2", container_format="bare", copy_from=image.image_addr)
    except (Unauthorized):
        errors[i] = site.site_name + " Unauthorized"
    except (HTTPServiceUnavailable):
        errors[i] = site.site_name + " HTTPServiceUnavailable"

    ids[i] = image.id

def delete_image(deployed_image):
    """
    deletes an image from the site using the glanceclient
    """
    site_file = str(deployed_image.site.site_RC_file)

    # exports info from RC file
    RC_dict = export_RC_file(site_file)
    RC_dict['OS_PASSWORD'] = str(deployed_image.site.site_password)
    token, endpoint = get_token_and_ep(RC_dict)

    # gets the image from the image ID and then deletes it from the site
    glance = glclient.Client(endpoint=endpoint, token=token)
    image = glance.images.get(deployed_image.image_identity)
    image.delete()

def auto_delete_image(dep_image_list):
    """
    compares a given list of deployed images with those on the site
    and returns a list of images that are no longer deployed on the site
    """
    to_delete = []
    for dep_image in dep_image_list:
        # creates glance client for each deployed image
        site_file = str(dep_image.site.site_RC_file)
        RC_dict = export_RC_file(site_file)
        RC_dict['OS_PASSWORD'] = str(dep_image.site.site_password)
        token, endpoint = get_token_and_ep(RC_dict)
        glance = glclient.Client(endpoint=endpoint, token=token)
        # gets a list of the image ID's from the site
        images = list(glance.images.list())
        id_list = [image.id for image in images]
        # if the image ID is no longer on the site, add it to a list of images to delete
        if dep_image.image_identity not in id_list:
            to_delete.append(dep_image.image_identity)
    return to_delete

# not used
# does not work for the DAIR site, AmbiguousEndpoint error because the client
# does not know whether to connect to Alberta or Quebec site
def launch_instance(name, deployed_image, flavor):
    """
    launches an instance from the deployed image with a name and flavor using the novaclient
    """
    # from deployed image get site's RC file, image ID
    site_file = str(deployed_image.site.site_RC_file)
    image_id = str(deployed_image.image_identity)

    # export info from RC file (doesn't work with endpoint and token?)
    RC_dict = export_RC_file(site_file)
    RC_dict['OS_PASSWORD'] = str(deployed_image.site.site_password)

    # get a nova client and image using deployed image ID
    nova = nvclient.Client(RC_dict['OS_USERNAME'], RC_dict['OS_PASSWORD'], RC_dict['OS_TENANT_NAME'], RC_dict['OS_AUTH_URL'])
    image = nova.images.find(id=image_id)
    # create instance with deployed image image and give it a name and flavor
    instance = nova.servers.create(name=name, image=image, flavor=flavor)
    return instance.id

# not used
# does not work for the DAIR site, AmbiguousEndpoint error because the client
# does not know whether to connect to Alberta or Quebec site
def terminate_instance(instance):
    """
    terminates the instance from the site using the novaclient
    """
    # from instance get the site's RC file, instance ID
    site_file = str(instance.deployed_image.site.site_RC_file)
    instance_id = str(instance.instance_identity)

    # export info from RC file
    RC_dict = export_RC_file(site_file)
    RC_dict['OS_PASSWORD'] = str(instance.deployed_image.site.site_password)

    # get nova client and instance and then delete it
    nova = nvclient.Client(RC_dict['OS_USERNAME'], RC_dict['OS_PASSWORD'], RC_dict['OS_TENANT_NAME'], RC_dict['OS_AUTH_URL'])
    instance = nova.servers.find(id=instance_id)
    instance.delete()

