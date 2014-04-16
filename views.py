from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.core.files import File
from django.core.files.base import ContentFile
from django.contrib.auth.views import logout_then_login
from django.contrib.auth.decorators import login_required

from vmdist.models import EC2_Cred
from openstack_utils import convert_image, create_image, delete_image, auto_delete_image
from ec2_utils import verify_cred, bundle_image, create_ami, delete_ami, auto_delete_ami
from keystoneclient.apiclient.exceptions import Unauthorized
import os, json, threading
import time, sys

@login_required
def jsonhandler(request):
    """
    parses through json message and executes the appropriate command
    returns back data to callback as a json string
    """
    user = request.user
    req = request.POST['jsonMsg']
    jsondata = json.loads(req)

    data, errors = {}, {}
    dep_list = []
    op = str(jsondata['op'])

    # op get_deployments: gets a list of deployments and all image + sites combinations
    if (op == 'get_deployments'):
        if (jsondata['deployments'] == 'init'):
            data['init'] = "True"
        else:
            data['init'] = "False"
        data['op'] = "get_deployments"
        data['deployments'] = get_latest_deployments(request)
        data['all'] = get_all(request)
    # op update: deploys and deletes images from sites
    elif (op == 'update'):
        data['op'] = "update"
        new_deployments = jsondata['deployments']['new_deployments']
        curr_deployments = get_deployments(request)[0]
        filter_deployments(request, new_deployments, curr_deployments, errors)
        data['deployments'] = get_deployments(request)
        data['all'] = get_all(request)
    else:
        print "Not an operation"

    data['errors'] = errors.values();

    jsonstr = json.dumps(data)
    return HttpResponse(jsonstr)

def get_latest_deployments(request):
    """
    gets the most current list of deployed images from sites
    """
    # sorts deployments by cloud types
    user = request.user
    to_delete, openstack_deployments, ec2_deployments = [], [], []
    dep_image_list = user.deployed_image_set.all()
    for dep_image in dep_image_list:
        site = dep_image.site
        if site.site_type == 'openstack':
            openstack_deployments.append(dep_image)
        elif site.site_type == 'ec2':
            ec2_deployments.append(dep_image)

    # gets a list of images that were deleted manually on Openstack and EC2
    auto_delete_image(openstack_deployments, to_delete)
    try:
        cred = user.ec2_cred
        auto_delete_ami(ec2_deployments, to_delete, cred)
    except Exception:
        # no EC2 credentials registered
        pass

    # deletes the above list of images from the models
    for image_ID in to_delete:
        dep_image = user.deployed_image_set.get(image_identity=image_ID)
        dep_image.delete()

    return get_deployments(request)
  
def get_deployments(request):
    """
    gets deployments in a dictionary format
    """
    user = request.user
    # gets list of deployments in the form: [{'image':['site1','site2'],...}]
    images = get_images(request)
    tmp_list = user.deployed_image_set.all()
    dep_list = []
    deployment = {}
    for image in images:
        sites = []
        for dep in tmp_list:
            if image == str(dep.image):
                sites.append(str(dep.site.site_name))
        deployment[image] = sites
    dep_list.append(deployment)
    return dep_list

def get_images(request):
    """
    gets a list of all images
    """
    user = request.user
    images = user.image_set.all()
    image_list = []
    for image in images:
        image_list.append(str(image))
    return image_list

def get_sites(request):
    """
    gets a list of all sites
    """
    user = request.user
    sites = user.site_set.all()
    site_list = []
    for site in sites:
        site_list.append(str(site))
    return site_list

def get_all(request):
    """
    gets all image and site combinations in a list
    in the form [{'image':['site1','site2']}, ... }]
    """
    complete_list = []
    for image in get_images(request):
        dep = {}
        dep[image] = get_sites(request)
        complete_list.append(dep)
    return complete_list

def filter_deployments(request, new_d, curr_d,  errors):
    """
    compares the list of new deployments to the old list
    sends deployments to either be deployed or deleted
    """
    to_deploy = []
    to_delete = []

    # creates a list of image-sites to deploy
    for key in new_d.keys():
        for site in new_d[key]:
            if site not in curr_d[key]:
                entry = {}
                entry[key] = site
                to_deploy.append(entry)

    # creates a list of image-sites to delete
    for key in curr_d.keys():
        for site in curr_d[key]:
            if site not in new_d[key]:
                entry = {} 
                entry[key] = site
                to_delete.append(entry)

    deploy_images(request, to_deploy, errors)
    delete_images(request, to_delete)

def deploy_images(request, deployments, errors):
    """
    attaches each deployment onto a thread and runs the threads
    images are then deployed using glanceclient or boto
    stores the new deployed image in the model database
    """
    user = request.user
    images, sites, tasks = [], [], []
    ids, buckets = {}, {}

    # appends threads for each image-site deployment
    for i in range(len(deployments)):
        image = user.image_set.get(image_name=deployments[i].keys()[0])
        site = user.site_set.get(site_name=deployments[i].values()[0])
        if site.site_type == 'openstack':
            # deploys to openstack site
            t1 = threading.Thread(target=create_image, args=(image, site, ids, errors, i))
            images.append(image)
            sites.append(site)
            tasks.append(t1)
        elif image.bundled == True and site.site_type == 'ec2':
            # deploys to ec2 site
            cred = user.ec2_cred
            t2 = threading.Thread(target=create_ami, args=(image, site, cred, ids, buckets, i))
            images.append(image)
            sites.append(site)
            tasks.append(t2)
        elif image.bundled == False and site.site_type == 'ec2':
            # if the user wanted to deploy to ec2 but the image was not yet bundled
            errors[i] = image.image_name + " Not Bundled"

    # starts and joins threads
    for task in tasks:
        task.start()
    for task in tasks:
        task.join()

    # adds deploymemts to database with ids dict holding deployment ID
    for i in range(len(deployments)):
        if i not in errors.keys():
            image = images[i]
            name = images[i].image_name
            ID = ids[i]
            site = sites[i]
            if site.site_type == 'openstack':
                deployed_image = user.deployed_image_set.create(deployed_image_name=name, image=image, image_identity=ID, site=site)
            elif site.site_type == 'ec2':
                bucket = buckets[i]
                deployed_image = user.deployed_image_set.create(deployed_image_name=name, image=image, image_identity=ID, site=site, bucket=bucket)

def delete_images(request, deployments):
    """
    deletes each image in deployments from the given site with glance or boto
    removes the deployed image from the model database
    """
    user = request.user
    for dep in deployments:
        image = dep.keys()[0]
        site = dep.values()[0]
        image_choice = user.image_set.get(image_name=image)
        site_choice = user.site_set.get(site_name=site)
        deployed_image_choice = user.deployed_image_set.get(image=image_choice, site=site_choice)
        if site_choice.site_type == 'openstack':
            delete_image(deployed_image_choice)
        elif site_choice.site_type == 'ec2':
            cred = user.ec2_cred
            delete_ami(deployed_image_choice, cred)
        deployed_image_choice.delete()

@login_required
def home(request):
    """
    renders user's home page
    """
    return render_to_response("vmdist/home.html", {'user':request.user})

def logout_user(request):
    """
    logs user out and redirects to login page
    """
    return logout_then_login(request)

@login_required
def images(request):
    return render_to_response("vmdist/images.html", {'user':request.user})

@login_required
def sites(request):
    return render_to_response("vmdist/sites.html", {'user':request.user})

@login_required
def help(request):
    return render_to_response("vmdist/help.html", {'user':request.user})

@login_required
def image_added(request):
    """
    add the user's image file or addr to the model database and saves to repo
    """
    user = request.user
    file_list = request.FILES.getlist('image_file')
    file_name_list = request.POST.getlist('file_name')
    file_format_list = request.POST.getlist('file_format')
    for file, file_name, file_format in zip(file_list, file_name_list, file_format_list):
        user.image_set.create(image_file=file, image_name=file_name, format=file_format)

    addr_list = request.POST.getlist('image_addr')
    addr_name_list = request.POST.getlist('addr_name')
    addr_format_list = request.POST.getlist('addr_format')
    for addr, addr_name, addr_format in zip(addr_list, addr_name_list, addr_format_list):
        if addr != "":
            user.image_set.create(image_addr=addr, image_name=addr_name, format=addr_format)

    return render_to_response("vmdist/images.html", {'user':user})

@login_required
def image_removed(request):
    """
    removes the user's image from the model database and deletes from repo
    if the image was bundled for EC2 it will also delete the manifest and parts
    """
    user = request.user
    image_ids = request.POST.getlist('image')
    for image_id in image_ids:
        image_choice = user.image_set.get(pk=image_id)
        if image_choice.image_file != "":
            os.remove(str(image_choice.image_file))
        if image_choice.bundled == True:
            os.remove(str(image_choice.image_file) + '.manifest.xml')
            i = 0
            while os.path.exists(str(image_choice.image_file) + '.part.' + str(i)):
                os.remove(str(image_choice.image_file) + '.part.' + str(i))
                i += 1
        image_choice.delete()
    return render_to_response("vmdist/images.html", {'user':user})

@login_required
def site_added(request):
    """
    adds openstack sites to model database with the user's site RC file and password
    """
    user = request.user
    name_list = request.POST.getlist('site_name')
    file_list = request.FILES.getlist('site_file')
    password_list = request.POST.getlist('password')
    for name, file, password in zip(name_list, file_list, password_list):
        user.site_set.create(site_name=name, site_RC_file=file, site_password=password, token="", endpoint="", site_type='openstack')
    return render_to_response("vmdist/sites.html", {'user':user})

@login_required
def site_removed(request):
    """
    removes openstack sites from model database and deletes the RC file
    """
    user = request.user
    site_ids = request.POST.getlist('site')
    for site_id in site_ids:
        site_choice = user.site_set.get(pk=site_id)
        if site_choice.site_type == 'openstack':
            os.remove(str(site_choice.site_RC_file))
        site_choice.delete()
    return render_to_response("vmdist/sites.html", {'user':user})

@login_required
def ec2_added(request):
    """
    adds EC2 credentials to user so they can deploy onto EC2 clouds
    if the access and secret key are verified, it will add all EC2 site regions
    """
    user = request.user
    account = request.POST['account']
    ak = request.POST['access_key']
    sk = request.POST['secret_key']
    cert = request.FILES['cert']
    pk = request.FILES['pk']

    if (verify_cred(ak, sk)):
        cred = EC2_Cred.objects.create(user=user, account=account, access_key=ak, secret_key=sk, cert=cert, private_key=pk)
        cred.save()

        ec2_sites = ['Ireland', 'N_Virginia', 'N_California', 'Oregon',
                     'Singapore', 'Sydney', 'Tokyo', 'Sao_Paulo']
        for site in ec2_sites:
            name = "EC2-" + site
            user.site_set.create(site_name=name, site_type='ec2')
        return render_to_response("vmdist/sites.html", {'user':user})
    else:
        error = "Access key or secret key is unauthorized. Please try again."
        return render_to_response("vmdist/sites.html", {'user':user, 'error':error})

@login_required
def ec2_removed(request):
    """
    removes EC2 credentials and removes any EC2 site regions still left
    """
    user = request.user
    cred = user.ec2_cred
    os.remove(str(cred.cert))
    os.remove(str(cred.private_key))
    cred.account = ""
    cred.delete()
    sites = user.site_set.all()
    for site in sites:
        if site.site_type == 'ec2':
            site.delete()
    return render_to_response("vmdist/sites.html", {'user':user})

@login_required
def image_bundled(request):
    """
    bundles image files saved in repo to deploy onto EC2 clouds
    """
    user = request.user
    name = str(user)
    image = user.image_set.get(pk=request.POST['image'])
    cred = user.ec2_cred
    bundle_image(name, image, cred)
    image.bundled = True
    image.save()
    return render_to_response("vmdist/images.html", {'user':user})

@login_required
def image_converted(request):
    """
    converts image into another format
    """
    user = request.user
    image = user.image_set.get(pk=request.POST['image'])
    to_format = str(request.POST['file_format'])
    # makes a converted version of image in top level
    to_file = convert_image(image, to_format)
    f = open(to_file)
    image_file = File(f)
    name = str(image) + '-' + to_format
    # stores converted image in the database making copy in the user's folder
    user.image_set.create(image_file=image_file, image_name=name, format=to_format)
    # deletes the temporary converted file in top level
    os.remove(to_file)
    return render_to_response("vmdist/images.html", {'user':user})
