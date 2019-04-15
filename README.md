# dri-loris-extras
Additional classes for the Loris IIIF image server for DRI use.

## DRIHttpAuthorizer

Sends an HTTP HEAD request to the DRI application to check if an image is accessible or not.
In order to be available to IIIF the object containing the image must be published, and the access
controls must be set to allow public access to the object's assets.

```
[authorizer]
   impl = 'loris.dri_http_authorizer.DRIHttpAuthorizer'
   authorized_url = '...' # auth endpoint of the DRI app
```

## RadosS3Resolver

Resolves an identifier into a Rados S3 gateway URL.

```
[resolver]
   impl = 'loris.rados_s3_resolver.RadosS3Resolver'
   access_key = ...
   secret_key = ...
   uri_resolvable = True
   endpoint = '...' # hostname of the Rados gateway
   bucket = '...' # bucket prefix
   ssl_check = False
   cache_root = '/tmp/loris/tmp/cache'
   src_img_root = '/tmp/loris/tmp/images'
   ident_suffix = '...' # appended to the ident to form the filename of the image
   default_format = 'jpg'
   [[extension_map]]
      jpeg = 'jpg'
      tiff = 'tif'
```
