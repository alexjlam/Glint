from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.views import logout_then_login
from django.contrib.auth.decorators import login_required
from openstack_utils import create_image, delete_image, auto_delete_image, launch_instance, terminate_instance
from keystoneclient.apiclient.exceptions import Unauthorized
import os, json, threading


@login_required
def jsonhandler(request):
    """
    parses throught json message and executes the appropriate command
    returns back data to callback as a json string
    """
    user = request.user
    req = request.POST['jsonMsg']
    #print "REQ", req
    jsondata = json.loads(req)

    #print type(jsondata)
    #print "loaded json data", jsondata

    data = {}
    dep_list = []
    op = str(jsondata['op'])
    #print op
    #test = jsondata['deployments']
    #print test['to_deploy']
    errors = {}

    #try except Unauthorized HttpResponse not used
    try:
        # op get_deployments: gets a list of deployments and all image + sites combinations
        if (op == 'get_deployments'):
            if (jsondata['deployments'] == 'init'):
                data['init'] = "True"
            else:
                data['init'] = "False"
            data['op'] = "get_deployments"
            data['deployments'] = get_deployments(request)
            data['all'] = get_all(request)
        # op compare: gets a list of deployments only
        elif (op == "compare"):
            data['op'] = "compare"
            data['deployments'] = get_deployments(request)
        # op update: deploys and deletes images from sites
        elif (op == 'update'):
            data['op'] = "update"
            new_deployments = jsondata['deployments']['new_deployments']
            curr_deployments = jsondata['deployments']['curr_deployments']
            latest_deployments = get_deployments(request)
            filter_deployments(request, new_deployments, curr_deployments, latest_deployments[0], errors)
            data['deployments'] = get_deployments(request)
            data['all'] = get_all(request)
        # op get_images: gets a list of all images
        elif (op == 'get_images'):
            data['op'] = "get_images"
            data['images'] = get_images(request)
        else:
            print "Not an operation"

        data['errors'] = errors.values();

        #print "ALL DATA", data
        jsonstr = json.dumps(data)
        #print jsonstr
        return HttpResponse(jsonstr)
    except(Unauthorized):
        return HttpResponse("Unauthorized")

def get_deployments(request):
    """
    gets the most current list of deployed images in a dict format
    """
    # updates model if any images have been deleted from the site
    user = request.user
    dep_image_list = user.deployed_image_set.all()
    to_delete = auto_delete_image(dep_image_list)
    for image_ID in to_delete:        
        dep_image = user.deployed_image_set.get(image_identity=image_ID)
        dep_image.delete()

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

def filter_deployments(request, new_d, curr_d, latest_d, errors):
    """
    compares the list of new deployments to the old list
    sends deployments to either be deployed or deleted
    """
    to_deploy = []
    to_delete = []

    # creates a list of image-sites to deploy
    for key in new_d.keys():
        for site in new_d[key]:
            # in the case where a image was deleted off a site
            # and it was not updated on the website yet, it will
            # not reupload the image to that site
            if site not in latest_d[key] \
            and site not in curr_d[key]:
                entry = {}
                entry[key] = site
                to_deploy.append(entry)

    for key in latest_d.keys():
        for site in latest_d[key]:
            if site not in new_d[key]:
                entry = {} 
                entry[key] = site
                to_delete.append(entry)

    deploy_images(request, to_deploy, errors)
    delete_images(request, to_delete)

def deploy_images(request, deployments, errors):
    """
    attaches each deployment onto a thread and runs the threads
    images are then deployed using glanceclient
    stores the new deployed image in the model database
    """
    user = request.user
    images, sites, tasks = [], [], []
    ids = {}

    # appends threads for each image-site deployment
    for i in range(len(deployments)):
        image = user.image_set.get(image_name=deployments[i].keys()[0])
        site = user.site_set.get(site_name=deployments[i].values()[0])
        t = threading.Thread(target=create_image, args=(image, site, ids, errors, i))
        images.append(image)
        sites.append(site)
        tasks.append(t)

    # starts and joins threads
    for t in tasks:
        t.start()
    for t in tasks:
        t.join()

    # adds deploymemts to database with ids dict holding deployment ID
    for i in range(len(deployments)):
        if i not in errors.keys():
            image = images[i]
            name = images[i].image_name
            ID = ids[i]
            site = sites[i]
            deployed_image = user.deployed_image_set.create(deployed_image_name=name, image=image, image_identity=ID, site=site)

def delete_images(request, deployments):
    """
    deletes each image in deployments from the given site with glance
    removes the deployed image from the model database
    """
    user = request.user
    for dep in deployments:
        image = dep.keys()[0]
        site = dep.values()[0]
        image_choice = user.image_set.get(image_name=image)
        site_choice = user.site_set.get(site_name=site)
        deployed_image_choice = user.deployed_image_set.get(image=image_choice, site=site_choice)
        delete_image(deployed_image_choice)
        deployed_image_choice.delete()

@login_required
def home(request):
    """
    renders user's home page
    """
    #return render_to_response("openstack/test.html")
    return render_to_response("openstack/home.html", {'user':request.user})

def logout_user(request):
    """
    logs user out and redirects to login page
    """
    return logout_then_login(request)

@login_required
def images(request):
    return render_to_response("openstack/images.html", {'user':request.user})

@login_required
def sites(request):
    return render_to_response("openstack/sites.html", {'user':request.user})

# not being used, currently generating token for each create/delete
@login_required
def get_token(request):
    user = request.user
    return HttpResponse("you got a token")

# not used
@login_required
def deploy(request):
    """
    renders user's deploy page
    """
    return render_to_response("openstack/deploy.html", {'user':request.user})

# not used
@login_required
def image_deployed(request):
    """
    deploys the user's image files to various sites using glance api
    """
    user = request.user
    name = request.POST['name']
    # gets the image and list of database ids for each site and iterates through them and deploys on each site
    image_choice = user.image_set.get(pk=request.POST['image'])
    site_ids = request.POST.getlist('site')
    if site_ids:
        for site in site_ids:
            # gets the appropriate site from the database id
            site_choice = user.site_set.get(pk=site)
            try:
                print image_choice
                # sends image and site selected to create with glance and stores in model
                #image_id = create_image(image_choice, site_choice)
                deployed_image = user.deployed_image_set.create(deployed_image_name=image_choice.image_name, image=image_choice, image_identity=image_id, site=site_choice)
            except (Unauthorized):
                return HttpResponse("You are not authorized to deploy an image to that site. Check that your password is correct.")
        return render_to_response("openstack/image_deployed.html", {'user':user})
    else:
        return HttpResponse("You didn't select any sites")

# not used
@login_required
def delete(request):
    """
    renders user's delete page
    """
    return render_to_response("openstack/delete.html", {'user':request.user})

# not used
@login_required
def image_deleted(request):
    """
    deletes indicated deployed images created by the user using glance api
    """
    user = request.user
    # gets the list of database ids for each image and iterates through them and deletes
    image_ids = request.POST.getlist('image')
    if image_ids:
        for image_id in image_ids:
            # gets the appropriate deployed image from the database id
            deployed_image_choice = user.deployed_image_set.get(pk=image_id)
            try:
                # sends deployed image selected to delete with glance and deletes from model
                delete_image(deployed_image_choice)
                deployed_image_choice.delete()
            except (Unauthorized):
                return HttpResponse("You are not authorized to delete an image from that site. Check that your password is correct.")
        return render_to_response("openstack/image_deleted.html", {'user':user})
    else:
        return HttpResponse("You didn't select any images")

# not used
@login_required
def launch(request):
    """
    renders user's launch page for instances
    """
    return render_to_response("openstack/launch.html", {'user':request.user})

# not used
@login_required
def instance_launched(request):
    """
    launches instance with a name and flavor from the user and stores the instance in a model
    """
    user = request.user
    name = request.POST['name']
    deployed_image = user.deployed_image_set.get(pk=request.POST['image'])
    flavor = request.POST['flavor']
    instance_id = launch_instance(name, deployed_image, flavor)
    instance = user.instance_set.create(instance_name=name, deployed_image=deployed_image, instance_identity=instance_id)
    return render_to_response("openstack/instance_launched.html", {'user':user, 'instance':instance})

# not used
@login_required
def terminate(request):
    """
    renders user's terminate page for instances
    """
    return render_to_response("openstack/terminate.html", {'user':request.user})

# not used
@login_required
def instance_terminated(request):
    """
    terminates each instance selected and deletes instance from model
    """
    user = request.user
    # gets the list of database ids for each instance and iterates through them and terminates
    instance_ids = request.POST.getlist('instance')
    if instance_ids:
        for instance_id in instance_ids:
            # gets the appropriate instance from the database id
            instance = user.instance_set.get(pk=instance_id)
            try:
                # sends instance selected to terminate with nova and deletes from the model
                terminate_instance(instance)
                instance.delete()
            except (Unauthorized):
                return HttpResponse("You are not authorized to terminate from that site. Check that your password is correct.")
        return render_to_response("openstack/instance_terminated.html", {'user':user})
    else:
        return HttpResponse("You didn't select any instances")

@login_required
def image_added(request):
    """
    add the user's image file or addr to the model database and saves to repo
    """
    user = request.user
    file_list = request.FILES.getlist('image_file')
    for file in file_list:
        user.image_set.create(image_file=file, image_name=str(file))

    addr_list = request.POST.getlist('image_addr')
    for addr in addr_list:
        if addr != "":
            user.image_set.create(image_addr=addr, image_name=str(addr))
    return render_to_response("openstack/images.html", {'user':user})

@login_required
def image_removed(request):
    """
    removes the user's image from the model database and deletes from repo
    """
    user = request.user
    image_ids = request.POST.getlist('image')
    for image_id in image_ids:
        image_choice = user.image_set.get(pk=image_id)
        if image_choice.image_file != "":
            os.remove(str(image_choice.image_file))
        image_choice.delete()
    return render_to_response("openstack/images.html", {'user':user})

@login_required
def site_added(request):
    """
    add the user's site RC file and stores the site password to the model database and saves to repo
    """
    user = request.user
    name_list = request.POST.getlist('site_name')
    file_list = request.FILES.getlist('site_file')
    password_list = request.POST.getlist('password')
    for name, file, password in zip(name_list, file_list, password_list):
        user.site_set.create(site_name=name, site_RC_file=file, site_password=password)
    return render_to_response("openstack/sites.html", {'user':user})

@login_required
def site_removed(request):
    """
    removes the user's site RC file from the model database and deletes from repo
    """
    user = request.user
    site_ids = request.POST.getlist('site')
    for site_id in site_ids:
        site_choice = user.site_set.get(pk=site_id)
        os.remove(str(site_choice.site_RC_file))
        site_choice.delete()
    return render_to_response("openstack/sites.html", {'user':user})

