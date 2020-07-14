"""
Test the enterprise support utils.
"""


import mock
import ddt

from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.features.enterprise_support.utils import get_enterprise_learner_portals
from openedx.features.enterprise_support.tests import FEATURES_WITH_ENTERPRISE_ENABLED
from openedx.features.enterprise_support.tests.factories import EnterpriseCustomerUserFactory
from student.tests.factories import UserFactory


@ddt.ddt
@override_settings(FEATURES=FEATURES_WITH_ENTERPRISE_ENABLED)
@skip_unless_lms
class TestEnterpriseUtils(TestCase):
    """
    Test enterprise support utils.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory.create(password='password')
        super(TestEnterpriseUtils, cls).setUpTestData()

    @ddt.data(
        ('notfoundpage', 0),
    )
    @ddt.unpack
    def test_enterprise_customer_for_request_called_on_404(self, resource, expected_calls):
        """
        Test enterprise customer API is not called from 404 page
        """
        self.client.login(username=self.user.username, password='password')

        with mock.patch(
            'openedx.features.enterprise_support.api.enterprise_customer_for_request'
        ) as mock_customer_request:
            self.client.get(resource)
            self.assertEqual(mock_customer_request.call_count, expected_calls)

    def test_get_enterprise_learner_portals(self):
        """
        Test that only enabled enterprise portals are returned
        """
        EnterpriseCustomerUserFactory(user_id=self.user.id)
        with mock.patch(
            'openedx.features.enterprise_support.api.get_enterprise_learner_data'
        ) as mock_get_enterprise_learner_data:
            mock_get_enterprise_learner_data.return_value = [
                {
                    'enterprise_customer': {
                        'name': 'Enabled Customer',
                        'enable_learner_portal': True,
                        'branding_configuration': {
                            'enterprise_slug': 'enabled_customer',
                            'logo': 'enabled_logo',
                        },
                    },
                },
                {
                    'enterprise_customer': {
                        'name': 'Disabled Customer',
                        'enable_learner_portal': False,
                        'branding_configuration': {
                            'enterprise_slug': 'disabled_customer',
                            'logo': 'disabled_logo',
                        },
                    },
                }
            ]
            portals = get_enterprise_learner_portals(self.user)
            self.assertEqual(len(portals), 1)
            self.assertDictEqual(portals[0], {
                'name': 'Enabled Customer',
                'slug': 'enabled_customer',
                'logo': 'enabled_logo',
            })
