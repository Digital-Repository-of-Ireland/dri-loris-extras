from __future__ import absolute_import

from logging import getLogger
import requests

from contextlib import closing

from .webapp import LorisRequest
from .authorizer import _AbstractAuthorizer
from .loris_exception import ConfigError

logger = getLogger(__name__)

class DRIHttpAuthorizer(_AbstractAuthorizer):
    """
    Makes an HTTP HEAD call for authentication.
    """

    def __init__(self, config):
        super(DRIHttpAuthorizer, self).__init__(config)
        self._validate_config(config)
        self.authorized_url = config.get('authorized_url', '')

    def _validate_config(self, config):
        mandatory_keys = ['authorized_url']
        missing_keys = [key for key in mandatory_keys if key not in config]

        if missing_keys:
            raise ConfigError(
                'Missing mandatory parameters for %s: %s' %
                (type(self).__name__, ','.join(missing_keys))
            )

    def is_protected(self, info):
        return True

    def is_authorized(self, info, request):
        auth_params = None

        if 'Authorization' in request.headers:
            header = request.headers.get('Authorization')
            auth_params = self._extract_credentials(header)

        loris_request = LorisRequest(request)
        request_type = loris_request.request_type

        if request_type == 'info':
          action = 'info'
        elif request_type == 'image':
          action = 'show'
        else:
          action = 'info'

        auth_fp = "%s/%s?method=%s" % (self.authorized_url, loris_request.ident, action)
        if auth_params is not None:
            auth_fp = auth_fp + auth_params

        try:
            with closing(requests.head(auth_fp, verify=False)) as response:
                if response.status_code is 200:
                    return {"status": "ok"}
                else:
                    return {"status": "deny"}

        except requests.exceptions.MissingSchema as ms:
            message = 'Server Side Error: Error making authentication request.'
            logger.error(message)
            return {"status": "deny"}

    def get_services_info(self, info):
        return {"service": {}}

    def _extract_credentials(self, header):
        auth_header = base64.b64decode(header.replace('Basic','').strip()).decode('ascii').split(':')
        auth_params = '&user_email=%s&user_token=%s' % (auth_header[0], auth_header[1])
        return auth_params

