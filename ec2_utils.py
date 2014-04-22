#!/usr/bin/env python

from boto.s3.connection import S3Connection
import boto.ec2
import boto.exception
import subprocess, os, time

regions = {'EC2-Ireland':['EU','eu-west-1'],
           'EC2-N_Virginia':['','us-east-1'],
           'EC2-N_California':['us-west-1','us-west-1'],
           'EC2-Oregon':['us-west-2','us-west-2'],
           'EC2-Singapore':['ap-southeast-1','ap-southeast-1'],
           'EC2-Sydney':['ap-southeast-2','ap-southeast-2'],
           'EC2-Tokyo':['ap-northeast-1','ap-northeast-1'],
           'EC2-Sao_Paulo':['sa-east-1','sa-east-1']}

def verify_cred(ak, sk):
    """
    checks if access and secrey key works
    """
    test = boto.ec2.connect_to_region(region_name='us-west-1', aws_access_key_id=ak, aws_secret_access_key=sk)
    try:
        test.get_all_images(owners='self')
        return True
    except(boto.exception.EC2ResponseError):
        return False

def bundle_image(user, image, cred):
    """
    bundles the image into a manifest and parts for upload to EC2 site
    """
    account = str(cred.account)
    cert = str(cred.cert)
    pk = str(cred.private_key)
    image = str(image.image_file)
    dest = str(user)

    subprocess.check_output(['ec2-bundle-image', '-c', cert, '-k', pk, '-u', account, '-i', image, '-r', 'x86_64', '-d', dest])

def create_ami(image, site, cred, ids, buckets, i):
    """
    creates a bucket in the appropriate region and uploads bundle there
    after it registers the ami to that EC2 site
    """
    ak = str(cred.access_key)
    sk = str(cred.secret_key)

    region1 = regions[(site.site_name)][1]
    region2 = regions[(site.site_name)][0]

    #upload bundle to S3
    name = image.image_name

    region = regions[(site.site_name)][1]
    bucket = name + '-' + region1 + '-' + str(int(time.time())) #name-region-time

    s3conn = S3Connection(ak, sk)
    s3conn.create_bucket(bucket_name=bucket, location=region2)

    image = str(image.image_file)
    manifest = image + '.manifest.xml'
    subprocess.check_output(['ec2-upload-bundle', '-b', bucket, '-m', manifest, '-a', ak, '-s', sk, '--region', region1])

    # register bundle to EC2
    manifest = manifest.split('/')[-1]
    ec2conn = boto.ec2.connect_to_region(region_name=region, aws_access_key_id=ak, aws_secret_access_key=sk)
    imgloc = bucket + '/' + manifest
    img_id = ec2conn.register_image(name=name, image_location=imgloc)

    ids[i] = img_id
    buckets[i] = bucket

def delete_ami(deployment, cred):
    """
    deregisters ami and deletes the bucket and contents
    """
    ak = str(cred.access_key)
    sk = str(cred.secret_key)
    region = regions[str(deployment.site)][1]
    id = deployment.image_identity

    # connect to EC2 and deregister
    ec2conn = boto.ec2.connect_to_region(region_name=region, aws_access_key_id=ak, aws_secret_access_key=sk)
    amis = ec2conn.get_all_images(owners='self')
    id_list = [str(ami).split(':')[1] for ami in amis]
    if id in id_list:
        ec2conn.deregister_image(image_id=id)
    delete_bucket(deployment, ak, sk)

def delete_bucket(deployment, ak, sk):
    """
    deletes the bucket contents and then the bucket
    """
    s3conn = S3Connection(ak, sk)
    try:
        bucket = s3conn.get_bucket(bucket_name=deployment.bucket)
        keys = bucket.get_all_keys()
        bucket.delete_keys(keys)
        bucket.delete()
    except(boto.exception.S3ResponseError):
        # the bucket and contents were already deleted
        pass

def auto_delete_ami(deployments, to_delete, cred):
    """
    checks the list of deployments with those on EC2
    if it is no longer registered, it will delete the bucket
    and add to a list of deployments to delete
    """
    ak = cred.access_key
    sk = cred.secret_key
    for dep in deployments:
        site = dep.site
        region = regions[str(site)][1]
        ec2conn = boto.ec2.connect_to_region(region_name=region, aws_access_key_id=ak, aws_secret_access_key=sk)
        amis = ec2conn.get_all_images(owners='self')
        id_list = [str(ami).split(':')[1] for ami in amis]
        if dep.image_identity not in id_list:
            to_delete.append(dep.image_identity)
            delete_bucket(dep, ak, sk)

