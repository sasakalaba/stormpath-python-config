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


class MoveAPIKeyToClientAPIKeyStrategyTest(TestCase):
    def generateConfig(self, client_config={}):
        load_strategies = [
            # 1. We load the default configuration.
            LoadFileConfigStrategy(
                'tests/assets/default_config.yml', must_exist=True),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            # 3. We load apiKeyApiKey.json file with apiKey id and secret.
            LoadFileConfigStrategy('tests/assets/apiKeyApiKey.json'),
            LoadAPIKeyConfigStrategy('i-do-not-exist'),
            LoadFileConfigStrategy('i-do-not-exist'),
            LoadEnvConfigStrategy(prefix='STORMPATH'),
            # 7. Configuration provided through the SDK client constructor.
            ExtendConfigStrategy(extend_with=client_config)
        ]
        post_processing_strategies = [
            LoadAPIKeyFromConfigStrategy(), MoveAPIKeyToClientAPIKeyStrategy()]
        validation_strategies = [ValidateClientConfigStrategy()]

        cl = ConfigLoader(
            load_strategies, post_processing_strategies, validation_strategies)
        return cl.load()

    def test_move_api_key_to_client(self):
        """ Ensure that apiKey key is moved to client if set in config outer
            keys. """
        config = self.generateConfig()

        # Ensure that id and secret from outer apiKey key have beed loaded to
        # client key.
        self.assertEqual(
            config['client']['apiKey']['id'], 'MY_JSON_CONFIG_API_KEY_ID')
        self.assertEqual(
            config['client']['apiKey']['secret'],
            'MY_JSON_CONFIG_API_KEY_SECRET')
        self.assertFalse('apiKey' in config.keys())

    def test_move_api_key_to_client_missing_credentials(self):
        """ Ensure that missing id or secret will raise an Exception. """
        client_config = {'apiKey': {'foo': 'bar'}}

        with self.assertRaises(Exception) as error:
            self.generateConfig(client_config=client_config)
        self.assertEqual(
            error.exception.message, 'Unable to load apiKey id and secret.')
