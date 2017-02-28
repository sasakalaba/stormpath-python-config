from unittest import TestCase
from datetime import timedelta

from stormpath_config.strategies import EnrichIntegrationFromRemoteConfigStrategy
from stormpath_config.errors import ConfigurationError

from ..base import Application, Client


class EnrichIntegrationFromRemoteConfigStrategyTest(TestCase):
    def setUp(self):
        def _create_client_from_config(config):
            return Client([self.application])

        self.application = Application(
            'My named application',
            'https://api.stormpath.com/v1/applications/a')
        self.config = {
            'application': {
                'href': 'https://api.stormpath.com/v1/applications/a'
            },
            'web': {
                'social': {'facebook': {'enabled': False}},
                'register': {
                    'enabled': True,
                    'autoLogin': False
                }
            },
            'cookie': {
                'domain': 'cookie_domain',
                'duration': timedelta(minutes=30)
            }
        }
        self.ecfrcs = EnrichIntegrationFromRemoteConfigStrategy(
            client_factory=_create_client_from_config)

    def test_enrich_client_from_remote_config(self):
        config = self.ecfrcs.process(self.config)

        self.assertTrue('oAuthPolicy' in config['application'])
        self.assertEqual(config['application']['oAuthPolicy'], {
            'href': 'https://api.stormpath.com/v1/oAuthPolicies/a',
            'accessTokenTtl': 3600.0,
            'refreshTokenTtl': 5184000.0,
            'spHttpStatus': 200,
        })
        self.assertEqual(config['passwordPolicy'], {
            'minSymbol': 0,
            'minUpperCase': 1,
            'minLength': 8,
            'spHttpStatus': 200,
            'minNumeric': 1,
            'minLowerCase': 1,
            'minDiacritic': 0,
            'maxLength': 100
        })
        self.assertEqual(config['web']['social'], {
            'facebook': {'enabled': False},
            'google': {
                'providerId': 'google',
                'clientId': 'id',
                'clientSecret': 'secret',
                'enabled': True,
                'spHttpStatus': 200,
                'uri': '/callbacks/google',
                'redirectUri': 'https://myapplication.com/authenticate'
            }
        })
        self.assertEqual(config['web'], {
            'social': {
                'facebook': {'enabled': False},
                'google': {
                    'providerId': 'google',
                    'clientId': 'id',
                    'clientSecret': 'secret',
                    'enabled': True,
                    'spHttpStatus': 200,
                    'uri': '/callbacks/google',
                    'redirectUri': 'https://myapplication.com/authenticate'
                }
            },
            'changePassword': {'enabled': True},
            'forgotPassword': {'enabled': True},
            'verifyEmail': {'enabled': False},
            'register': {'autoLogin': False, 'enabled': True}
        })


class ValidateTest(EnrichIntegrationFromRemoteConfigStrategyTest):
    """Ensure that our config passes final validation."""

    def setUp(self):
        super(ValidateTest, self).setUp()
        self.config['web']['social'] = {
            'google': {'enabled': False},
            'facebook': {'enabled': False}
        }
        self.config['web']['register']['autoLogin'] = False
        self.config['web']['verifyEmail'] = {'enabled': False}

    def test_social_enabled_and_emtpy(self):
        # Ensure that social_enabled_and empty returns proper boolean values.

        social_config = {
            'enabled': True,
            'clientId': 'xxx',
            'clientSecret': 'yyy'
        }

        # Empty config.
        self.assertFalse(self.ecfrcs.social_enabled_and_empty({}))

        # Invalid config value.
        self.assertFalse(self.ecfrcs.social_enabled_and_empty(True))

        # Social enabled with id and secret.
        self.assertFalse(self.ecfrcs.social_enabled_and_empty(social_config))

        # Social enabled but missing secret.
        social_config.pop('clientSecret')
        self.assertTrue(self.ecfrcs.social_enabled_and_empty(social_config))

    def test_application(self):
        # Ensure that validation fails if application settings are missing or
        # invalid.

        # Invalid application href.
        self.config['application']['href'] = 'https://api.stormpath.com/v1/a'
        with self.assertRaises(ConfigurationError) as error:
            self.ecfrcs.validate(self.config)
        self.assertEqual(
            error.exception.message,
            'Application HREF "https://api.stormpath.com/v1/a" is not a ' +
            'valid Stormpath Application HREF.')

        # No application name or href.
        self.config['application'] = {}
        with self.assertRaises(ConfigurationError) as error:
            self.ecfrcs.validate(self.config)
        self.assertEqual(
            error.exception.message, 'Application cannot be empty.')

        # No application settings.
        self.config.pop('application')
        with self.assertRaises(ConfigurationError) as error:
            self.ecfrcs.validate(self.config)
        self.assertEqual(
            error.exception.message, 'Application cannot be empty.')

        # Ensure that we can resolve application by name.
        self.config['application'] = {'name': 'My named application'}
        self.ecfrcs.validate(self.config)

    def test_google_settings(self):
        # Ensure that validation fails if google config is invalid.

        # Turn off facebook social.
        self.config['web']['social'] = {'facebook': {'enabled': False}}

        # Empty google settings.
        self.config['web']['social']['google'] = {}
        with self.assertRaises(ConfigurationError) as error:
            self.ecfrcs.validate(self.config)
        self.assertEqual(
            error.exception.message,
            'You must define your Google app settings.'
        )

        # Enabled google settings, but otherwise empty.
        self.config['web']['social']['google']['enabled'] = True
        with self.assertRaises(ConfigurationError) as error:
            self.ecfrcs.validate(self.config)
        self.assertEqual(
            error.exception.message,
            'You must define your Google app settings.'
        )

        # Enabled and clientId provided, but secret missing.
        self.config['web']['social']['google']['clientId'] = 'xxx'
        with self.assertRaises(ConfigurationError) as error:
            self.ecfrcs.validate(self.config)
        self.assertEqual(
            error.exception.message,
            'You must define your Google app settings.'
        )

        # Now that we've configured things properly, it should work.
        self.config['web']['social']['google']['clientSecret'] = 'yyy'
        self.ecfrcs.validate(self.config)

    def test_facebook_settings(self):
        # Ensure that validation fails if facebook config is invalid.

        # Turn off google social.
        self.config['web']['social'] = {'google': {'enabled': False}}

        # No facebook settings.
        with self.assertRaises(ConfigurationError) as error:
            self.ecfrcs.validate(self.config)
        self.assertEqual(
            error.exception.message,
            'You must define your Facebook app settings.'
        )

        # Empty facebook settings.
        self.config['web']['social']['facebook'] = {}
        with self.assertRaises(ConfigurationError) as error:
            self.ecfrcs.validate(self.config)
        self.assertEqual(
            error.exception.message,
            'You must define your Facebook app settings.'
        )

        # Enabled facebook settings, but otherwise empty.
        self.config['web']['social']['facebook']['enabled'] = True
        with self.assertRaises(ConfigurationError) as error:
            self.ecfrcs.validate(self.config)
        self.assertEqual(
            error.exception.message,
            'You must define your Facebook app settings.'
        )

        # Enabled and clientId provided, but secret missing.
        self.config['web']['social']['facebook']['clientId'] = 'xxx'
        with self.assertRaises(ConfigurationError) as error:
            self.ecfrcs.validate(self.config)
        self.assertEqual(
            error.exception.message,
            'You must define your Facebook app settings.'
        )

        # Now that we've configured things properly, it should work.
        self.config['web']['social']['facebook']['clientSecret'] = 'yyy'
        self.ecfrcs.validate(self.config)

    def test_cookie_settings(self):
        # Ensure that validation fails if cookie settings are invalid.

        # Missing cookie settings.
        self.config.pop('cookie')
        with self.assertRaises(ConfigurationError) as error:
            self.ecfrcs.validate(self.config)
        self.assertEqual(
            error.exception.message, 'Cookie settings cannot be empty.')

        # Empty cookie settings.
        self.config['cookie'] = {}
        with self.assertRaises(ConfigurationError) as error:
            self.ecfrcs.validate(self.config)
        self.assertEqual(
            error.exception.message, 'Cookie settings cannot be empty.')

        # Invalid cookie domain.
        self.config['cookie'] = {'domain': 55}
        with self.assertRaises(ConfigurationError) as error:
            self.ecfrcs.validate(self.config)
        self.assertEqual(
            error.exception.message, 'Cookie domain must be a string.')

        # Invalid cookie duration.
        self.config['cookie'] = {
            'domain': '55',
            'duration': 55
        }

        with self.assertRaises(ConfigurationError) as error:
            self.ecfrcs.validate(self.config)
        self.assertEqual(
            error.exception.message, 'Cookie duration must be a string.')

        # Now that we've configured things properly, it should work.
        self.config['cookie'] = {
            'domain': 'cookie_domain',
            'duration': timedelta(minutes=1)
        }
        self.ecfrcs.validate(self.config)

    def test_verify_email_autologin(self):
        # Ensure that validation fails if both autologin and email verification
        # are enabled.

        # Turn on verify email and autologin.
        self.config['web']['register']['autoLogin'] = True
        self.config['web']['verifyEmail']['enabled'] = True

        with self.assertRaises(ConfigurationError) as error:
            self.ecfrcs.validate(self.config)
        self.assertEqual(
            error.exception.message,
            'Invalid configuration: stormpath.web.register.autoLogin is' +
            ' true, but the default account store of the specified' +
            ' application has the email verification workflow enabled.' +
            ' Auto login is only possible if email verification is' +
            ' disabled. Please disable this workflow on this' +
            ' application\'s default account store.')

        # Turn off one of the settings, and configuration should be valid.
        self.config['web']['register']['autoLogin'] = False
        self.ecfrcs.validate(self.config)

    def test_register_default_account_store(self):
        # Ensure that validation fails if register view is enabled, but default
        # account store mapping is missing.

        self.application.default_account_store_mapping = False
        with self.assertRaises(ConfigurationError) as error:
            self.ecfrcs.validate(self.config)
        self.assertEqual(
            error.exception.message,
            'No default account store is mapped to the specified ' +
            'application. A default account store is required for ' +
            'registration.'
        )

        # Now that we've configured things properly, it should work.
        self.application.default_account_store_mapping = object()
        self.ecfrcs.validate(self.config)
