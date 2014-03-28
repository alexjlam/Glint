#!/usr/bin/env python

import subprocess, re, os
from keystoneclient.v2_0 import client as keyclient
from keystoneclient.apiclient.exceptions import Unauthorized
from glanceclient.v1 import client as glclient
from glanceclient.exc import HTTPUnauthorized as BadToken

def convert_image(image, to_format):
    """
    makes a copy of the image in another format in top level
    """
    from_file = str(image.image_file)
    from_format = str(image.format)
    to_file = (os.path.splitext(from_file)[0] + '.' + to_format).split('/')[1]
    subprocess.check_output(['qemu-img', 'convert', '-f', from_format, '-O', to_format, from_file, to_file])
    return to_file

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

def update_token(site):
    """
    gets token and endpoint for site if it has not been set yet
    checks if token is expired, if it is then it will get a new one
    """
    site_file = str(site.site_RC_file)
    RC_dict = export_RC_file(site_file)
    RC_dict['OS_PASSWORD'] = str(site.site_password)

    if site.token == "":
        # obtain first token and endpoint
        site.token, site.endpoint = get_token_and_ep(RC_dict)
        site.save()

    glance = glclient.Client(endpoint=site.endpoint, token=site.token)

    try:
        # if token is good the test will be good
        test = list(glance.images.list())
    except(BadToken):
        # if token is bad then it will get an updated token
        site.token, endpoint = get_token_and_ep(RC_dict)
        site.save()

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
    format = image.format
    try:    
        update_token(site)
        # uses the token and endpoint to get a glanceclient
        glance = glclient.Client(endpoint=site.endpoint, token=site.token)
        # create an image with a file
        if image.image_file != "":
            image_file = str(image.image_file)
            with open(image_file) as fimage:
                image = glance.images.create(name=name, disk_format=format, container_format="bare", data=fimage)
        # creates an image with a website address
        else:
            image = glance.images.create(name=name, disk_format=format, container_format="bare", copy_from=image.image_addr)
    except (Unauthorized):
        errors[i] = site.site_name + " Unauthorized"
    #except (HTTPServiceUnavailable):
        #errors[i] = site.site_name + " HTTPServiceUnavailable"

    ids[i] = image.id

def delete_image(deployment):
    """
    deletes an image from the site using the glanceclient
    """
    site = deployment.site
    update_token(site)
    # gets the image from the image ID and then deletes it from the site
    glance = glclient.Client(endpoint=site.endpoint, token=site.token)
    images = list(glance.images.list())
    id_list = [image.id for image in images]
    # if the image is still on the site, it will delete it
    # else the image has already been deleted
    if deployment.image_identity in id_list:
        image = glance.images.get(deployment.image_identity)
        image.delete()

def auto_delete_image(deployments, to_delete):
    """
    compares a given list of deployed images with those on the site
    and adds to a list of images that are no longer deployed on the site
    """
    for dep in deployments:
        # creates glance client for each deployed image
        site = dep.site
        update_token(site)
        glance = glclient.Client(endpoint=site.endpoint, token=site.token)
        # gets a list of the image ID's from the site
        images = list(glance.images.list())
        id_list = [image.id for image in images]
        # if the image ID is no longer on the site, add it to a list of images to delete
        if dep.image_identity not in id_list:
            to_delete.append(dep.image_identity)

