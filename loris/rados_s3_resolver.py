from __future__ import absolute_import

from logging import getLogger

from os import environ

import boto
import boto.s3.connection

from .resolver import SimpleHTTPResolver
from .loris_exception import ResolverException

logger = getLogger(__name__)

class RadosS3Resolver(SimpleHTTPResolver):
    '''Rados S3 Gateway resolver that supports multiple configurable patterns for supported
    urls. Based on SimpleHTTPResolver.

    The configuration MUST contain
     * `cache_root`, which is the absolute path to the directory where source images
        should be cached.

    The configuration may also include the following settings, as used by
    SimpleHTTPResolver:
     * `default_format`, the format of images (will use content-type of
        response if not specified).
     * `head_resolvable` with value True, whether to make HEAD requests
        to verify object existence (don't set if using Fedora Commons
        prior to 3.8).  [Currently must be the same for all templates]
    '''
    def __init__(self, config):
        super(RadosS3Resolver, self).__init__(config)

        # inherited/required configs from simple http resolver
        self.head_resolvable = self.config.get('head_resolvable', False)
        self.default_format = self.config.get('default_format', None)
        self.ident_regex = self.config.get('ident_regex', False)
        if 'cache_root' in self.config:
            self.cache_root = self.config['cache_root']
        else:
            message = 'Server Side Error: Configuration incomplete and cannot resolve. Missing setting for cache_root.'
            logger.error(message)
            raise ResolverException(500, message)

        self.bucket = self.config.get('bucket', None)
        self.access_key = self.config.get('access_key', environ.get('AWS_ACCESS_KEY_ID', None))
        self.secret_key = self.config.get('secret_key', environ.get('AWS_SECRET_ACCESS_KEY', None))
        self.endpoint = self.config.get('endpoint', None)
        self.ident_suffix = self.config.get('ident_suffix', None)
        self.delimiter = self.config.get('delimiter', ':')
        self.extension_map = self.config['extension_map']

        # required for simplehttpresolver
        # all templates are assumed to be uri resolvable
        self.uri_resolvable = True

        self.ssl_check = self.config.get('ssl_check', True)

    def format_from_ident(self, ident, potential_format):
        format = super(RadosS3Resolver, self).format_from_ident(ident, potential_format)
        format = format.lower()
        format = self.extension_map.get(format, format)

        return format

    def is_resolvable(self, ident):
        ident = unquote(ident)

        if self.delimiter not in ident:
            return False

        bucket_suffix, keyname = ident.split(self.delimiter, 1)
        keys = keyname.split('/')

        if len(keys) > 1:
            return False
        else:
            return super(RadosS3Resolver, self).is_resolvable(ident)

    def _web_request_url(self, ident):
        # only split identifiers that look like template ids;
        # ignore other requests (e.g. favicon)
        if self.delimiter not in ident:
            return

        bucket_suffix, keyname = ident.split(self.delimiter, 1)

        if self.ident_suffix and keyname != bucket_suffix:
            keyname = u'{0}_{1}'.format(keyname, self.ident_suffix)

        bucketname = '.'.join([self.bucket,bucket_suffix])
        logger.debug('Getting img from Rados S3. bucketname, keyname: %s, %s' % (bucketname, keyname))
        conn = boto.connect_s3(
              aws_access_key_id = self.access_key,
              aws_secret_access_key = self.secret_key,
              host = self.endpoint,
              is_secure=self.ssl_check,               # uncomment if you are not using ssl
              calling_format = boto.s3.connection.OrdinaryCallingFormat(),
        )

        bucket = conn.get_bucket(bucketname)
        list = bucket.list(prefix=keyname)
        for key in list:
            # Get the generic options
            options = self.request_options()
            return(key.generate_url(3600, query_auth=True), options)

        return None

    def request_options(self):
        # currently no username/password supported
        return {}
