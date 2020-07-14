""" Contenstore API v1 URLs. """

from django.urls import re_path

from . import views
from openedx.core.constants import COURSE_ID_PATTERN

app_name = 'v1'

urlpatterns = [
    re_path(
        r'^proctored_exam_settings/{}$'.format(COURSE_ID_PATTERN),
        views.proctored_exam_settings,
        name="proctored_exam_settings"
    ),
]
