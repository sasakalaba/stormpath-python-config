from unittest import TestCase
from stormpath_config.loader import ConfigLoader
from stormpath_config.strategies import (
    LoadAPIKeyConfigStrategy,
    LoadFileConfigStrategy,
    LoadEnvConfigStrategy,
    ExtendConfigStrategy,
    LoadAPIKeyFromConfigStrategy,
    ValidateClientConfigStrategy,
    MoveAPIKeyToClientAPIKeyStrategy)


class LoadAPIKeyFromConfigStrategyTest(TestCase):
    def test_api_key_from_config_with_lesser_loading_order(self):
        """ Ensure that api key and secret are properly loaded from file. """

        load_strategies = [
            # 1. We load the default configuration.
            LoadFileConfigStrategy(
                'tests/assets/default_config.yml', must_exist=True),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            # 3. We load apiKeyFile.yml file with apiKey.properties file.
            LoadFileConfigStrategy('tests/assets/apiKeyFile.yml'),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            LoadFileConfigStrategy('i-do-not-exist'),
            LoadEnvConfigStrategy(prefix='STORMPATH'),
            # 7. Configuration provided through the SDK client constructor.
            ExtendConfigStrategy(extend_with={})
        ]
        post_processing_strategies = [
            LoadAPIKeyFromConfigStrategy(), MoveAPIKeyToClientAPIKeyStrategy()]
        validation_strategies = [ValidateClientConfigStrategy()]

        cl = ConfigLoader(
            load_strategies, post_processing_strategies, validation_strategies)
        config = cl.load()

        self.assertEqual(
            config['client']['apiKey']['id'], 'API_KEY_PROPERTIES_ID')
        self.assertEqual(
            config['client']['apiKey']['secret'], 'API_KEY_PROPERTIES_SECRET')
        self.assertFalse('file' in config['client']['apiKey'])
