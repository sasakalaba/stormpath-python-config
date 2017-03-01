"""Tests for the ConfigLoader class."""


from os import environ
from unittest import TestCase
from mock import patch
from stormpath_config.loader import ConfigLoader
from stormpath_config.strategies import (
    ExtendConfigStrategy,
    LoadAPIKeyConfigStrategy,
    LoadAPIKeyFromConfigStrategy,
    LoadEnvConfigStrategy,
    LoadFileConfigStrategy,
    ValidateClientConfigStrategy,
    MoveAPIKeyToClientAPIKeyStrategy,
    MoveSettingsToConfigStrategy
)


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
            LoadFileConfigStrategy(
                'tests/assets/default_config.yml', must_exist=True),

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
            MoveAPIKeyToClientAPIKeyStrategy()
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
        cl = ConfigLoader(
            self.load_strategies,
            self.post_processing_strategies,
            self.validation_strategies
        )
        config = cl.load()

        self.assertEqual(
            config['client']['apiKey']['id'], 'CLIENT_CONFIG_API_KEY_ID')
        self.assertEqual(
            config['client']['apiKey']['secret'],
            'CLIENT_CONFIG_API_KEY_SECRET')
        self.assertEqual(
            config['client']['cacheManager']['defaultTtl'], 302)
        self.assertEqual(
            config['client']['cacheManager']['defaultTti'], 303)
        self.assertEqual(config['application']['name'], 'CLIENT_CONFIG_APP')


class OverridingStrategiesTest(TestCase):
    """
    This testing class will simulate the loading process for stormpath-flask.
    """
    def setUp(self):
        self.post_processing_strategies = [
            LoadAPIKeyFromConfigStrategy(),
            MoveAPIKeyToClientAPIKeyStrategy()
        ]
        self.validation_strategies = [
            ValidateClientConfigStrategy()
        ]

    def setLoadingStrategies(self, assets={}):
        # Our custom strategy loader builder.

        load_strategies = [
            # 1. Default configuration.
            LoadFileConfigStrategy(
                assets.get('default_config', 'empty'), must_exist=True),

            # 2. apiKey.properties file from ~/.stormpath directory.
            LoadAPIKeyConfigStrategy(assets.get('home_apiKey', 'empty')),

            # 3. stormpath.json file from ~/.stormpath directory.
            LoadFileConfigStrategy(assets.get('home_stormpath_json', 'empty')),

            # 3.1. stormpath.yaml file from ~/.stormpath directory.
            LoadFileConfigStrategy(assets.get('home_stormpath_yaml', 'empty')),

            # 4. apiKey.properties file from application directory.
            LoadAPIKeyConfigStrategy(assets.get('app_apiKey', 'empty')),

            # 5. stormpath.json file from application directory.
            LoadFileConfigStrategy(assets.get('app_stormpath_json', 'empty')),

            # 5.1. stormpath.yaml file from application directory.
            LoadFileConfigStrategy(assets.get('app_stormpath_yaml', 'empty')),

            # 6. Environment variables.
            LoadEnvConfigStrategy(prefix=assets.get('env_prefix', 'empty')),

            # 7. Configuration provided through the SDK client constructor.
            ExtendConfigStrategy(extend_with=assets.get('client_config', {})),

            # 8. Configuration provided 'STORMPATH' prefix in outer config.
            MoveSettingsToConfigStrategy(config=assets.get('outer_config', {}))
        ]
        return load_strategies

    def getConfig(self):
        # Returns the final config.

        cl = ConfigLoader(
            self.load_strategies,
            self.post_processing_strategies,
            self.validation_strategies
        )
        return cl.load()

    def test_strategies_override_01(self):
        # Ensure that original config file is loaded.

        # Enable only the first asset.
        self.load_strategies = self.setLoadingStrategies({
            'default_config': 'tests/assets/default_config.yml'
        })

        # Ensure that config file was loaded and an error was raised, since
        # our testing asset does not have apiKey credentials.
        with self.assertRaises(ValueError) as error:
            self.getConfig()
        self.assertEqual(
            error.exception.message, 'API key ID and secret are required.')

    def test_strategies_override_02(self):
        # Ensure that apiKey.properties file from HOME directory will override
        # any settings from previous config sources.

        # Enable first two assets.
        self.load_strategies = self.setLoadingStrategies({
            'default_config': 'tests/assets/default_config.yml',
            'home_apiKey': 'tests/assets/apiKey.properties'
        })
        config = self.getConfig()

        # Ensure that default config file was properly loaded.
        self.assertEqual(
            config['client']['baseUrl'], 'https://api.stormpath.com/v1')
        self.assertIsNone(config['application']['name'])

        # Ensure that apiKey.properties overwrote previous api key id and
        # secret.
        self.assertEqual(
            config['client']['apiKey']['id'], 'API_KEY_PROPERTIES_ID')
        self.assertEqual(
            config['client']['apiKey']['secret'], 'API_KEY_PROPERTIES_SECRET')

    def test_strategies_override_03(self):
        # Ensure that stormpath.json file from HOME stormpath directory will
        # override any settings from previous config sources.

        # Enable first three assets.
        self.load_strategies = self.setLoadingStrategies({
            'default_config': 'tests/assets/default_config.yml',
            'home_apiKey': 'tests/assets/apiKey.properties',
            'home_stormpath_json': 'tests/assets/apiKeyApiKey.json'
        })
        config = self.getConfig()

        # Ensure that json asset overwrote previous api key id and secret.
        self.assertEqual(
            config['client']['apiKey']['id'], 'MY_JSON_CONFIG_API_KEY_ID')
        self.assertEqual(
            config['client']['apiKey']['secret'],
            'MY_JSON_CONFIG_API_KEY_SECRET')
        self.assertIsNone(config['client']['apiKey']['file'])

    def test_strategies_override_04(self):
        # Ensure that stormpath.yaml file from HOME stormpath directory will
        # override any settings from previous config sources.

        # Enable first four assets.
        self.load_strategies = self.setLoadingStrategies({
            'default_config': 'tests/assets/default_config.yml',
            'home_apiKey': 'tests/assets/apiKey.properties',
            'home_stormpath_json': 'tests/assets/apiKeyApiKey.json',
            'home_stormpath_yaml': 'tests/assets/apiKeyFile.yml',
        })
        config = self.getConfig()

        # Ensure that yaml asset overwrote previous api key id and secret.
        self.assertEqual(
            config['client']['apiKey']['id'], 'API_KEY_PROPERTIES_ID')
        self.assertEqual(
            config['client']['apiKey']['secret'], 'API_KEY_PROPERTIES_SECRET')
        self.assertFalse('file' in config['client']['apiKey'])

    def test_strategies_override_05(self):
        # Ensure that apiKey.properties file from app directory will override
        # any settings from previous config sources.

        # Enable first five assets.
        self.load_strategies = self.setLoadingStrategies({
            'default_config': 'tests/assets/default_config.yml',
            'home_apiKey': 'tests/assets/apiKey.properties',
            'home_stormpath_json': 'tests/assets/apiKeyApiKey.json',
            'home_stormpath_yaml': 'tests/assets/apiKeyFile.yml',
            'app_apiKey': 'tests/assets/secondary_apiKey.properties',
        })
        config = self.getConfig()

        # Ensure that apiKey.properties asset overwrote previous api key id
        # and secret.
        self.assertEqual(
            config['client']['apiKey']['id'],
            'SECONDARY_API_KEY_PROPERTIES_ID')
        self.assertEqual(
            config['client']['apiKey']['secret'],
            'SECONDARY_API_KEY_PROPERTIES_SECRET')

    def test_strategies_override_06(self):
        # Ensure that stormpath.json file will override any settings from
        # previous config sources.

        # Enable first six assets.
        self.load_strategies = self.setLoadingStrategies({
            'default_config': 'tests/assets/default_config.yml',
            'home_apiKey': 'tests/assets/apiKey.properties',
            'home_stormpath_json': 'tests/assets/apiKeyApiKey.json',
            'home_stormpath_yaml': 'tests/assets/apiKeyFile.yml',
            'app_apiKey': 'tests/assets/secondary_apiKey.properties',
            'app_stormpath_json': 'tests/assets/stormpath.json'
        })
        config = self.getConfig()

        # Ensure that stormpath.json asset overwrote previous settings.
        self.assertEqual(
            config['client']['baseUrl'], 'https://api.stormpath.com/v3')
        self.assertEqual(config['application']['name'], 'MY_JSON_APP')

    def test_strategies_override_07(self):
        # Ensure that stormpath.yaml file will override any settings from
        # previous config sources.

        # Enable first seven assets.
        self.load_strategies = self.setLoadingStrategies({
            'default_config': 'tests/assets/default_config.yml',
            'home_apiKey': 'tests/assets/apiKey.properties',
            'home_stormpath_json': 'tests/assets/apiKeyApiKey.json',
            'home_stormpath_yaml': 'tests/assets/apiKeyFile.yml',
            'app_apiKey': 'tests/assets/secondary_apiKey.properties',
            'app_stormpath_json': 'tests/assets/stormpath.json',
            'app_stormpath_yaml': 'tests/assets/stormpath.yml',
        })
        config = self.getConfig()

        # Ensure that stormpath.yaml asset overwrote previous settings.
        self.assertEqual(
            config['client']['baseUrl'], 'https://api.stormpath.com/v2')
        self.assertEqual(config['application']['name'], 'MY_APP')

    def test_strategies_override_08(self):
        # Ensure that stormpath environment variables will override any
        # settings from previous config sources.

        # Enable first eight assets.
        self.load_strategies = self.setLoadingStrategies({
            'default_config': 'tests/assets/default_config.yml',
            'home_apiKey': 'tests/assets/apiKey.properties',
            'home_stormpath_json': 'tests/assets/apiKeyApiKey.json',
            'home_stormpath_yaml': 'tests/assets/apiKeyFile.yml',
            'app_apiKey': 'tests/assets/secondary_apiKey.properties',
            'app_stormpath_json': 'tests/assets/stormpath.json',
            'app_stormpath_yaml': 'tests/assets/stormpath.yml',
            'env_prefix': 'STORMPATH'
        })
        environ['STORMPATH_APPLICATION_NAME'] = 'MY_ENVIRON_APP'
        config = self.getConfig()

        # Ensure that stormpath environment variables overwrote previous
        # settings.
        self.assertEqual(config['application']['name'], 'MY_ENVIRON_APP')

    def test_strategies_override_09(self):
        # Ensure that client constructor settings will override any settings
        # from previous config sources.

        # Enable all assets.
        self.load_strategies = self.setLoadingStrategies({
            'default_config': 'tests/assets/default_config.yml',
            'home_apiKey': 'tests/assets/apiKey.properties',
            'home_stormpath_json': 'tests/assets/apiKeyApiKey.json',
            'home_stormpath_yaml': 'tests/assets/apiKeyFile.yml',
            'app_apiKey': 'tests/assets/secondary_apiKey.properties',
            'app_stormpath_json': 'tests/assets/stormpath.json',
            'app_stormpath_yaml': 'tests/assets/stormpath.yml',
            'env_prefix': 'STORMPATH',
            'client_config': {
                'application': {
                    'name': 'CLIENT_CONFIG_APP'
                }
            }
        })
        config = self.getConfig()

        # Ensure that client config asset overwrote previous settings.
        self.assertEqual(config['application']['name'], 'CLIENT_CONFIG_APP')

    def test_strategies_override_10(self):
        # Ensure that settings from outer config with 'STORMPATH' prefix will
        # override any settings from previous config sources.

        # Enable all assets.
        self.load_strategies = self.setLoadingStrategies({
            'default_config': 'tests/assets/default_config.yml',
            'home_apiKey': 'tests/assets/apiKey.properties',
            'home_stormpath_json': 'tests/assets/apiKeyApiKey.json',
            'home_stormpath_yaml': 'tests/assets/apiKeyFile.yml',
            'app_apiKey': 'tests/assets/secondary_apiKey.properties',
            'app_stormpath_json': 'tests/assets/stormpath.json',
            'app_stormpath_yaml': 'tests/assets/stormpath.yml',
            'env_prefix': 'STORMPATH',
            'client_config': {
                'application': {
                    'name': 'CLIENT_CONFIG_APP'
                }
            },
            'outer_config': {
                'STORMPATH_BASE_TEMPLATE': 'stormpath_base_template',
                'STORMPATH_APPLICATION': 'OUTER_STORMPATH_APP'
            }
        })
        config = self.getConfig()

        # Ensure that outer config asset overwrote previous settings.
        self.assertEqual(config['base_template'], 'stormpath_base_template')
        self.assertEqual(config['application']['name'], 'OUTER_STORMPATH_APP')
