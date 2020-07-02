# pylint: disable=abstract-method
"""
Progress Tab Serializers
"""

from rest_framework import serializers
from lms.djangoapps.course_home_api.outline.v1.serializers import CourseBlockSerializer


class CoursewareSummarySerializer(serializers.Serializer):
    """
    Serializer
    """
    blocks = serializers.SerializerMethodField()

    def get_blocks(self, blocks):
        return [
            {
                'display_name': chapter['display_name'],
                'url_name': chapter['url_name'],
                'sections': [
                    {
                        'display_name': section.display_name,
                        'url_name': section.url_name,
                        'percent_graded': section.percent_graded,
                        'graded_total': {
                            'first_attempted': section.graded_total.first_attempted,
                            'possible': section.graded_total.possible,
                            'graded': section.graded_total.graded,
                            'earned': section.graded_total.earned,
                        },
                        'format': section.format,
                        'due': section.due,
                        'override': section.override,  # this may not actually be serializable
                        'show_correctness': section.show_correctness,
                        'graded': section.graded,
                        'problem_scores': [
                            {
                                'earned': score.earned,
                                'possible': score.possible,
                            }
                            for score in section.problem_scores.values()
                        ],
                        'show_grades': section.show_grades(self.context['staff_access'])
                    }
                    for section in chapter['sections']
                ],
            }
            for chapter in blocks
        ]


class ProgressTabSerializer(serializers.Serializer):
    """
    Serializer
    """
    course_blocks = CourseBlockSerializer()
    enrollment_mode = serializers.CharField()
    courseware_summary = CoursewareSummarySerializer()
