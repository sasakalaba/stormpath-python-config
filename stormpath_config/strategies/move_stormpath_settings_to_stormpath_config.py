from ..helpers import _extend_dict
from .load_apikey_from_config import LoadAPIKeyFromConfigStrategy


class MoveStormpathSettingsToStormpathConfig(object):
    """
    Checks the outer config and retrieves values whose keys start with
    'STORMPATH' prefix, and stores them in the configuration object properly.
    """
    STORMPATH_PREFIX = 'STORMPATH'
    KEY_DELIMITER = '*'
    MAPPINGS = {
        'APPLICATION': 'application',
        'API_KEY_ID': 'client*apiKey*id',
        'API_KEY_SECRET': 'client*apiKey*secret',
        'API_KEY_FILE': 'client*apiKey*file',
        'ENABLE_FACEBOOK': 'web*social*facebook*enabled',
        'ENABLE_GOOGLE': 'web*social*google*enabled',
        'FACEBOOK_LOGIN_URL': 'web*social*facebook*login_url',
        'GOOGLE_LOGIN_URL': 'web*social*google*login_url',
        'CACHE': 'cache',
        'BASE_TEMPLATE': 'base_template',
        'COOKIE_DOMAIN': 'cookie*domain',
        'COOKIE_DURATION': 'cookie*duration',
    }

    def set_key(self, config, key, value):
        """
        We use this method to properly map values into stormpath config object.
        Some values are nested, in which case we create sub-dictionaries if
        needed.
        """
        subkeys = key.split(self.KEY_DELIMITER)
        if len(subkeys) > 1:
            attr = subkeys.pop(-1)
            subdict = config
            for key in subkeys:
                subdict.setdefault(key, {})
                subdict = subdict[key]
            subdict[attr] = value
        else:
            config[key] = value

    def get_updated_config(self, config):
        """
        Creates a dictionary with new values whose keys are properly formated
        to fit into stormpath config object.
        """
        updated_config = {}
        for key, value in config.items():
            if key.startswith(self.STORMPATH_PREFIX):
                stormpath_key = self.MAPPINGS.get(key.split('STORMPATH_')[1])

                # Check the format of application information.
                if stormpath_key == 'application':
                    if 'https://api.stormpath.com/v1/applications' in value:
                        stormpath_key = 'application*href'
                    else:
                        stormpath_key = 'application*name'

                if stormpath_key:
                    self.set_key(updated_config, stormpath_key, value)

        if 'STORMPATH_API_KEY_FILE' in config.keys():
            load_api_from_config = LoadAPIKeyFromConfigStrategy()
            load_api_from_config.process(updated_config)

        return updated_config

    def process(self, config=None):
        if config is None:
            config = {}

        if config.get('stormpath'):
            updated_config = self.get_updated_config(config)
            _extend_dict(config['stormpath'], updated_config)

        return config
