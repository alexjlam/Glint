# Glint README

A virtual machine distribution service which deploys multiple images to multiple cloud sites at once. Currently supports Openstack and Amazon EC2 clouds.

## Summary

The user first uploads their own image file or website address to an image to store it in Glint.
To save an Openstack cloud, the user must supply their RC file and password for that cloud to store in Glint.
To save an Amazon EC2 cloud, the user can save their EC2 credentials to obtain all eight regions in EC2. They must also bundle their image file before they can deploy it.
The user is can then make changes to deploy (red to green) and delete (green to red) their images with the Deployments interface.
