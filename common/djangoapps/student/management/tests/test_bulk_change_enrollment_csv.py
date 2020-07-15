

import unittest
from tempfile import NamedTemporaryFile

import six
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from testfixtures import LogCapture

from course_modes.models import CourseMode
from course_modes.tests.factories import CourseModeFactory
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from student.models import BulkUpdatenrollmentConfiguration

LOGGER_NAME = 'student.management.commands.bulk_change_enrollment_csv'


class BulkChangeEnrollmentCSVTests(SharedModuleStoreTestCase):
    """
    Tests bulk_change_enrollmetn_csv command
    """
    def setUp(self):
        super(BulkChangeEnrollmentCSVTests, self).setUp()
        self.courses = []

        self.user_info = [
            ('amy', 'amy@pond.com', 'password'),
            ('rory', 'rory@theroman.com', 'password'),
            ('river', 'river@song.com', 'password')
        ]

        self.enrollments = []
        self.users = []

        for username, email, password in self.user_info:
            user = UserFactory.create(username=username, email=email, password=password)
            self.users.append(user)
            course = CourseFactory.create()
            CourseModeFactory.create(course_id=course.id, mode_slug=CourseMode.AUDIT)
            CourseModeFactory.create(course_id=course.id, mode_slug=CourseMode.VERIFIED)
            self.courses.append(course)
            self.enrollments.append(CourseEnrollment.enroll(user, course.id, mode=CourseMode.AUDIT))

    def _write_test_csv(self, csv, lines):
        """Write a test csv file with the lines provided"""
        csv.write(b"course_id,user,mode,\n")
        for line in lines:
            csv.write(six.b(line))
        csv.seek(0)
        return csv

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_user_not_exist(self):
        """Verify that warning is logged for non existing user."""
        with NamedTemporaryFile() as csv:
            csv = self._write_test_csv(csv, lines=["course-v1:edX+DemoX+Demo_Course,user,audit\n"])

            with LogCapture(LOGGER_NAME) as log:
                call_command("bulk_change_enrollment_csv", "--csv_file_path={}".format(csv.name))
                log.check(
                    (
                        LOGGER_NAME,
                        'WARNING',
                        'Invalid or non-existent user [user]'
                    )
                )

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_invalid_course_key(self):
        """Verify in case of invalid course key warning is logged."""
        with NamedTemporaryFile() as csv:
            csv = self._write_test_csv(csv, lines=["Demo_Course,river,audit\n"])

            with LogCapture(LOGGER_NAME) as log:
                call_command("bulk_change_enrollment_csv", "--csv_file_path={}".format(csv.name))
                log.check(
                    (
                        LOGGER_NAME,
                        'WARNING',
                        'Invalid or non-existent course id [Demo_Course]'
                    )
                )

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_already_enrolled_student(self):
        """ Verify in case if a user is already enrolled warning is logged."""
        with NamedTemporaryFile() as csv:
            csv = self._write_test_csv(csv, lines=[str(self.courses[0].id) + ",amy,audit\n"])

            with LogCapture(LOGGER_NAME) as log:
                call_command("bulk_change_enrollment_csv", "--csv_file_path={}".format(csv.name))
                log.check(
                    (
                        LOGGER_NAME,
                        'INFO',
                        'Student [{}] is already enrolled in Course [{}] in mode [{}].'.format(
                            'amy',
                            str(self.courses[0].id),
                            'audit',
                        )
                    )
                )

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_bulk_enrollment(self):
        """ Test all users are enrolled using the command."""
        lines = [
            str(enrollment.course.id) + "," + str(enrollment.user.username) + ",verified\n"
            for enrollment in self.enrollments
        ]

        with NamedTemporaryFile() as csv:
            csv = self._write_test_csv(csv, lines=lines)
            call_command("bulk_change_enrollment_csv", "--csv_file_path={}".format(csv.name))

        for enrollment in self.enrollments:
            new_enrollment = CourseEnrollment.get_enrollment(user=enrollment.user, course_key=enrollment.course)
            self.assertEqual(new_enrollment.is_active, True)
            self.assertEqual(new_enrollment.mode, CourseMode.VERIFIED)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_bulk_enrollment_from_config_model(self):
        """ Test all users are enrolled using the config model."""
        lines = "course_id,user,mode\n"
        for enrollment in self.enrollments:
            str(enrollment.course.id) + "," + str(enrollment.user.username) + ",verified\n"

        csv_file = SimpleUploadedFile(name='test.csv', content=lines.encode('utf-8'), content_type='text/csv')
        BulkUpdatenrollmentConfiguration.objects.create(enabled=True, csv_file=csv_file)
        call_command("bulk_change_enrollment_csv")

        for enrollment in self.enrollments:
            new_enrollment = CourseEnrollment.get_enrollment(user=enrollment.user, course_key=enrollment.course)
            self.assertEqual(new_enrollment.is_active, True)
            self.assertEqual(new_enrollment.mode, CourseMode.VERIFIED)
