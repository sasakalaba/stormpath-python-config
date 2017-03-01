from unittest import TestCase
from stormpath_config.strategies import MoveSettingsToConfigStrategy


class MoveSettingsToConfigStrategyTest(TestCase):
    def setUp(self):
        self.stormpath_config = {
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
        self.config = {'stormpath': self.stormpath_config}

    def test_regular_mapping(self):
        """
        Ensures that settings with 'STORMPATH' prefix are properly
        copied to stormpath config object.
        """
        self.config['STORMPATH_BASE_TEMPLATE'] = 'flask_stormpath/base.html'

        move_stormpath_settings = MoveSettingsToConfigStrategy(
            config=self.config)
        move_stormpath_settings.process(self.config['stormpath'])

        self.assertEqual(
            self.config['stormpath']['base_template'],
            'flask_stormpath/base.html')

    def test_multiple_key_mapping(self):
        """
        Ensures that multiple key settings with 'STORMPATH' prefix are
        properly copied to stormpath config object.
        """
        self.config['STORMPATH_ENABLE_FACEBOOK'] = False

        move_stormpath_settings = MoveSettingsToConfigStrategy(
            config=self.config)
        move_stormpath_settings.process(self.config['stormpath'])

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

        move_stormpath_settings = MoveSettingsToConfigStrategy(
            config=self.config)
        move_stormpath_settings.process(self.config['stormpath'])

        self.assertNotIn('foo', self.config['stormpath'])

    def test_non_stormpath_key_mapping(self):
        """
        Ensures that settings without 'STORMPATH' prefix are skipped.
        """
        self.config['FOO'] = 'bar'

        move_stormpath_settings = MoveSettingsToConfigStrategy(
            config=self.config)
        move_stormpath_settings.process(self.config['stormpath'])

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

        move_stormpath_settings = MoveSettingsToConfigStrategy(
            config=self.config)
        move_stormpath_settings.process(self.config['stormpath'])

        self.assertEqual(
            self.config['stormpath']['base_template'],
            'flask_stormpath/base.html')
        self.assertEqual(
            self.config['stormpath']['web']['social']['facebook']['enabled'],
            False)

    def test_parsing_application_name_href(self):
        """
        Ensure that our strategy can properly differentiate between name and
        href stored in STORMPATH_APPLICATION.
        """

        # Ensure that application name is stored as name.
        self.config['STORMPATH_APPLICATION'] = 'app_name'

        move_stormpath_settings = MoveSettingsToConfigStrategy(
            config=self.config)
        move_stormpath_settings.process(self.config['stormpath'])

        self.assertEqual(
            self.config['stormpath']['application']['name'], 'app_name')

        # Ensure that application uri is stored as href.
        self.config['STORMPATH_APPLICATION'] = (
            'https://api.stormpath.com/v1/applications/foobar')

        move_stormpath_settings = MoveSettingsToConfigStrategy(
            config=self.config)
        move_stormpath_settings.process(self.config['stormpath'])

        self.assertEqual(
            self.config['stormpath']['application']['href'],
            'https://api.stormpath.com/v1/applications/foobar')
