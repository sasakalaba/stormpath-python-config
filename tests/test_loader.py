"""Tests for the ConfigLoader class."""


from os import environ
from unittest import TestCase

from mock import patch

from stormpath_config.loader import ConfigLoader
from stormpath_config.strategies import ExtendConfigStrategy, \
    LoadAPIKeyConfigStrategy, \
    LoadAPIKeyFromConfigStrategy, \
    LoadEnvConfigStrategy, \
    LoadFileConfigStrategy, \
    ValidateClientConfigStrategy


class ConfigLoaderTest(TestCase):
    def setUp(self):
        self.client_config = {
            'application': {
                'name': 'CLIENT_CONFIG_APP',
                'href': None
            },
            'client': {
                'apiKey': {
                    'id': 'CLIENT_CONFIG_API_KEY_ID',
                    'secret': 'CLIENT_CONFIG_API_KEY_SECRET',
                }
            }
        }

        self.load_strategies = [
            # 1. Default configuration.
            LoadFileConfigStrategy('tests/assets/default_config.yml', must_exist=True),

            # 2. apiKey.properties file from ~/.stormpath directory.
            LoadAPIKeyConfigStrategy('tests/assets/apiKey.properties'),

            # 3. stormpath.[json or yaml] file from ~/.stormpath
            #    directory.
            LoadFileConfigStrategy('tests/assets/stormpath.yml'),

            # 4. apiKey.properties file from application directory.
            LoadAPIKeyConfigStrategy('tests/assets/no_apiKey.properties'),

            # 5. stormpath.[json or yaml] file from application
            #    directory.
            LoadFileConfigStrategy('tests/assets/stormpath.json'),

            # 6. Environment variables.
            LoadEnvConfigStrategy(prefix='STORMPATH'),

            # 7. Configuration provided through the SDK client
            #    constructor.
            ExtendConfigStrategy(extend_with=self.client_config)
        ]
        self.post_processing_strategies = [
            # Post-processing: If the key client.apiKey.file isn't
            # empty, then a apiKey.properties file should be loaded
            # from that path.
            LoadAPIKeyFromConfigStrategy(),
        ]
        self.validation_strategies = [
            # Post-processing: Validation
            ValidateClientConfigStrategy()
        ]

    def test_empty_config_loader(self):
        cl = ConfigLoader()
        self.assertEqual(len(cl.load().keys()), 0)

    @patch.dict(environ, {
        'STORMPATH_CLIENT_APIKEY_ID': 'env api key id',
        'STORMPATH_CLIENT_APIKEY_SECRET': 'env api key secret',
        'STORMPATH_CLIENT_CACHEMANAGER_DEFAULTTTI': '303',
        'STORMPATH_APPLICATION_NAME': 'My app',
    })
    def test_config_loader(self):
        cl = ConfigLoader(self.load_strategies, self.post_processing_strategies, self.validation_strategies)
        config = cl.load()

        self.assertEqual(config['client']['apiKey']['id'], 'CLIENT_CONFIG_API_KEY_ID')
        self.assertEqual(config['client']['apiKey']['secret'], 'CLIENT_CONFIG_API_KEY_SECRET')
        self.assertEqual(config['client']['cacheManager']['defaultTtl'], 302)
        self.assertEqual(config['client']['cacheManager']['defaultTti'], 303)
        self.assertEqual(config['application']['name'], 'CLIENT_CONFIG_APP')

    def test_stormpath_key_loader(self):
        self.client_config['application']['name'] = 'STORMPATH_KEY_APP'
        self.load_strategies[6] = ExtendConfigStrategy(
            extend_with={'stormpath': self.client_config})
        cl = ConfigLoader(
            self.load_strategies,
            self.post_processing_strategies,
            self.validation_strategies
        )
        config = cl.load()

        self.assertEqual(config['application']['name'], 'STORMPATH_KEY_APP')
        self.assertFalse('stormpath' in config)


class OverridingStrategiesTest(TestCase):
    """
    This testing class will simulate the loading process for stormpath-flask.
    """
    def setUp(self):
        self.client_config = {}

    def test_strategies_override_01(self):
        # Ensure that original config file is loaded.

        # cl = ConfigLoader(
        #     self.load_strategies,
        #     self.post_processing_strategies,
        #     self.validation_strategies
        # )
        # config = cl.load()
        pass

    def test_strategies_override_02(self):
        # Ensure that apiKey.properties file from HOME directory will override
        # any settings from previous config sources.
        pass

    def test_strategies_override_03(self):
        # Ensure that stormpath.json file from HOME stormpath directory will
        # override any settings from previous config sources.
        pass

    def test_strategies_override_04(self):
        # Ensure that stormpath.yaml file from HOME stormpath directory will
        # override any settings from previous config sources.
        pass

    def test_strategies_override_05(self):
        # Ensure that apiKey.properties file will override any settings from
        # previous config sources.
        pass

    def test_strategies_override_06(self):
        # Ensure that stormpath.json file will override any settings from
        # previous config sources.
        pass

    def test_strategies_override_07(self):
        # Ensure that stormpath.yaml file will override any settings from
        # previous config sources.
        pass

    def test_strategies_override_08(self):
        # Ensure that stormpath environment variables will override any
        # settings from previous config sources.
        pass

    def test_strategies_override_09(self):
        # Ensure that client constructor settings will override any settings
        # from previous config sources.
        pass
