class MoveAPIKeyToClientAPIKeyStrategy(object):
    """ Represents a strategy that checks if our config has an outer key named
        `apiKey'. If it does, we move it to client.apiKey. """
    def process(self, config=None):
        if config is None:
            config = {}

        apiKey = config.get('apiKey', {})
        if apiKey:
            api_key_id = apiKey.get('id')
            api_key_secret = apiKey.get('secret')
            if not (api_key_id and api_key_secret):
                raise Exception('Unable to load apiKey id and secret.')

            config.setdefault('client', {})
            config['client'].setdefault('apiKey', {})
            config['client']['apiKey']['id'] = api_key_id
            config['client']['apiKey']['secret'] = api_key_secret

        config.pop('apiKey', {})
        return config
