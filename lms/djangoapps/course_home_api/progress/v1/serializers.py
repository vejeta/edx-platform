# pylint: disable=abstract-method
"""
Progress Tab Serializers
"""

from rest_framework import serializers
from lms.djangoapps.course_home_api.outline.v1.serializers import CourseBlockSerializer


class UserSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.CharField()
    is_staff = serializers.BooleanField()


class ProgressTabSerializer(serializers.Serializer):
    """
    Serializer
    """
    user = UserSerializer()
    course_blocks = CourseBlockSerializer()
    enrollment_mode = serializers.CharField()
