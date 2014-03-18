#!/usr/bin/env python

from boto.s3.connection import S3Connection
import boto.ec2
import subprocess, os, time

regions = {'EC2-Ireland':'eu-west-1',
           'EC2-N_Virginia':'us-east-1',
           'EC2-N_California':'us-west-1',
           'EC2-Oregon':'us-west-2',
           'EC2-Singapore':'ap-southeast-1',
           'EC2-Sydney':'ap-southeast-2',
           'EC2-Tokyo':'ap-northeast-1',
           'EC2-Sao_Paulo':'sa-east-1'}


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

    #upload bundle to S3
    name = str(image.image_name)

    region = regions[str(site)]
    bucket = name + '-' + region + '-' + str(time.time()) #name-region-time
    s3conn = S3Connection(ak, sk)
    s3conn.create_bucket(bucket_name=bucket, location=region)

    image = str(image.image_file)
    manifest = image + '.manifest.xml'
    subprocess.check_output(['ec2-upload-bundle', '-b', bucket, '-m', manifest, '-a', ak, '-s', sk, '--location', region])

    # register bundle to EC2
    manifest = manifest.split('/')[-1]
    conn = boto.ec2.connect_to_region(region, aws_access_key_id=ak, aws_secret_access_key=sk)
    imgloc = bucket + '/' + manifest
    img_id = conn.register_image(name=name, image_location=imgloc)

    ids[i] = img_id
    buckets[i] = bucket

def delete_ami(deployed_image, cred):

    # deregister AMI
    ak = str(cred.access_key)
    sk = str(cred.secret_key)
    region = regions[str(deployed_image.site)]
    conn = boto.ec2.connect_to_region(region, aws_access_key_id=ak, aws_secret_access_key=sk)
    id = deployed_image.image_identity
    conn.deregister_image(image_id=id)
    
    # delete all bucket contents and then the bucket
    s3conn = S3Connection(ak, sk)
    bucket = s3conn.get_bucket(bucket_name=deployed_image.bucket)
    keys = bucket.get_all_keys()
    bucket.delete_keys(keys)
    bucket.delete()

