from unittest import TestCase
from stormpath_config.strategies import (
    MoveStormpathSettingsToStormpathConfigStrategy)


class MoveStormpathSettingsToStormpathConfigStrategyTest(TestCase):
    def setUp(self):
        stormpath_config = {
            'client': {
                'apiKey': {'id': 'api key id', 'secret': 'api key secret'},
                'cacheManager': {'defaultTtl': 300, 'defaultTti': 300}
            },
            'web': {
                'social': {
                    'facebook': {
                        'scope': 'email',
                        'uri': '/callbacks/facebook'},
                    'google': {
                        'scope': 'email profile',
                        'uri': '/callbacks/google'}
                }
            }
        }
        self.config = {'stormpath': stormpath_config}

    def test_regular_mapping(self):
        """
        Ensures that settings with 'STORMPATH' prefix are properly
        copied to stormpath config object.
        """
        self.config['STORMPATH_BASE_TEMPLATE'] = 'flask_stormpath/base.html'

        move_stormpath_settings = MoveStormpathSettingsToStormpathConfigStrategy()
        move_stormpath_settings.process(self.config)

        self.assertEqual(
            self.config['stormpath']['base_template'],
            'flask_stormpath/base.html')

    def test_multiple_key_mapping(self):
        """
        Ensures that multiple key settings with 'STORMPATH' prefix are
        properly copied to stormpath config object.
        """
        self.config['STORMPATH_ENABLE_FACEBOOK'] = False

        move_stormpath_settings = MoveStormpathSettingsToStormpathConfigStrategy()
        move_stormpath_settings.process(self.config)

        self.assertEqual(
            self.config['stormpath']['web']['social']['facebook']['enabled'],
            False)

        # Ensure that other values form social_facebook are unaltered.
        self.assertEqual(
            self.config['stormpath']['web']['social']['facebook']['scope'],
            'email')
        self.assertEqual(
            self.config['stormpath']['web']['social']['facebook']['uri'],
            '/callbacks/facebook')

    def test_empty_key_mapping(self):
        """
        Ensures that settings with 'STORMPATH' prefix not specified in
        MAPPINGS are ignored.
        """
        self.config['STORMPATH_FOO'] = 'bar'

        move_stormpath_settings = MoveStormpathSettingsToStormpathConfigStrategy()
        move_stormpath_settings.process(self.config)

        self.assertNotIn('foo', self.config['stormpath'])

    def test_non_stormpath_key_mapping(self):
        """
        Ensures that settings without 'STORMPATH' prefix are skipped.
        """
        self.config['FOO'] = 'bar'

        move_stormpath_settings = MoveStormpathSettingsToStormpathConfigStrategy()
        move_stormpath_settings.process(self.config)

        self.assertNotIn('foo', self.config['stormpath'])

    def test_default_values(self):
        """
        Ensures that creating new values will override old values.
        """
        self.config['stormpath']['base_template'] = (
            'flask_stormpath/default_base.html')
        self.config['stormpath']['web']['social']['facebook']['enabled'] = True

        self.config['STORMPATH_BASE_TEMPLATE'] = 'flask_stormpath/base.html'
        self.config['STORMPATH_ENABLE_FACEBOOK'] = False

        move_stormpath_settings = MoveStormpathSettingsToStormpathConfigStrategy()
        move_stormpath_settings.process(self.config)

        self.assertEqual(
            self.config['stormpath']['base_template'],
            'flask_stormpath/base.html')
        self.assertEqual(
            self.config['stormpath']['web']['social']['facebook']['enabled'],
            False)

    def test_no_stormpath_config(self):
        """
        Ensure that missing stormpath config object won't break the
        application.
        """
        self.config['STORMPATH_BASE_TEMPLATE'] = 'flask_stormpath/base.html'
        self.config.pop('stormpath')

        move_stormpath_settings = MoveStormpathSettingsToStormpathConfigStrategy()
        move_stormpath_settings.process(self.config)

        self.assertEqual(
            self.config,
            {'STORMPATH_BASE_TEMPLATE': 'flask_stormpath/base.html'})

    def test_load_api_key_from_config_strategy(self):
        """
        Ensure that LoadAPIKeyFromConfigStrategy was called if api_key_file
        setting was specified with STORMPATH prefix.
        """
        self.config[
            'STORMPATH_API_KEY_FILE'] = 'tests/assets/apiKey.properties'

        move_stormpath_settings = MoveStormpathSettingsToStormpathConfigStrategy()
        move_stormpath_settings.process(self.config)

        self.assertEqual(
            self.config['stormpath']['client']['apiKey'],
            {'id': 'API_KEY_PROPERTIES_ID',
             'secret': 'API_KEY_PROPERTIES_SECRET'})

    def test_parsing_application_name_href(self):
        """
        Ensure that our strategy can properly differentiate between name and
        href stored in STORMPATH_APPLICATION.
        """

        # Ensure that application name is stored as name.
        self.config['STORMPATH_APPLICATION'] = 'app_name'

        move_stormpath_settings = MoveStormpathSettingsToStormpathConfigStrategy()
        move_stormpath_settings.process(self.config)

        self.assertEqual(
            self.config['stormpath']['application']['name'], 'app_name')

        # Ensure that application uri is stored as href.
        self.config['STORMPATH_APPLICATION'] = (
            'https://api.stormpath.com/v1/applications/foobar')

        move_stormpath_settings = MoveStormpathSettingsToStormpathConfigStrategy()
        move_stormpath_settings.process(self.config)

        self.assertEqual(
            self.config['stormpath']['application']['href'],
            'https://api.stormpath.com/v1/applications/foobar')
