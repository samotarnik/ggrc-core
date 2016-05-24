# Copyright (C) 2016 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

"""Tests for notifications for models with assignable mixin."""

from datetime import datetime
from freezegun import freeze_time
from mock import patch
from sqlalchemy import and_

from ggrc import db
from ggrc.models import Request
from ggrc.models import Notification
from ggrc.models import NotificationType
from integration.ggrc import TestCase
from integration.ggrc import api_helper


class TestAssignableNotification(TestCase):

  """Test setting notifications for assignable mixin."""

  def setUp(self):
    TestCase.setUp(self)
    self.client.get("/login")
    self._fix_notification_init()
    self.api_helper = api_helper.Api()

  def _fix_notification_init(self):
    """Fix Notification object init function.

    This is a fix needed for correct created_at field when using freezgun. By
    default the created_at field is left empty and filed by database, which
    uses system time and not the fake date set by freezugun plugin. This fix
    makes sure that object created in freeze_time block has all dates set with
    the correct date and time.
    """

    def init_decorator(init):
      """Wrapper for Notification init function."""

      def new_init(self, *args, **kwargs):
        init(self, *args, **kwargs)
        if hasattr(self, "created_at"):
          self.created_at = datetime.now()
      return new_init

    Notification.__init__ = init_decorator(Notification.__init__)

  @classmethod
  def _get_notifications(cls, sent=False, notif_type=None):
    """Get a notification query.

    Args:
      sent (boolean): flag to filter out only notifications that have been
        sent.
      notif_type (string): name of the notification type.

    Returns:
      sqlalchemy query for selected notifications.
    """
    if sent:
      notif_filter = Notification.sent_at.isnot(None)
    else:
      notif_filter = Notification.sent_at.is_(None)

    if notif_type:
      notif_filter = and_(notif_filter, NotificationType.name == notif_type)

    return db.session.query(Notification).join(NotificationType).filter(
        notif_filter
    )

  @patch("ggrc.notifications.common.send_email")
  def test_request_without_verifiers(self, _):
    """Test setting notification entries for simple requests.

    This function tests that each request gets an entry in the notifications
    table after it's been created.
    Second part of the tests is to make sure that request status does not add
    any new notification entries if the request does not have a verifier.
    """

    with freeze_time("2015-04-01"):

      self.assertEqual(self._get_notifications().count(), 0)
      self.import_file("request_full_no_warnings.csv")
      requests = {request.slug: request for request in Request.query}

      self.assertEqual(self._get_notifications().count(), 12)

      self.api_helper.delete(requests["Request 1"])
      self.api_helper.delete(requests["Request 11"])

      self.assertEqual(self._get_notifications().count(), 10)

      self.client.get("/_notifications/send_todays_digest")
      self.assertEqual(self._get_notifications().count(), 0)

      request = Request.query.get(requests["Request 9"].id)

      self.api_helper.modify_object(request, {"status": Request.FINAL_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(request, {"status": Request.START_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(request,
                                    {"status": Request.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(request, {"status": Request.FINAL_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(request,
                                    {"status": Request.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 0)

  @patch("ggrc.notifications.common.send_email")
  def test_request_with_verifiers(self, _):
    """Test notifications entries for declined requests.

    This tests makes sure there are extra notification entries added when a
    request has been declined.
    """

    with freeze_time("2015-04-01"):

      self.assertEqual(self._get_notifications().count(), 0)
      self.import_file("request_full_no_warnings.csv")
      requests = {request.slug: request for request in Request.query}

      self.assertEqual(self._get_notifications().count(), 12)

      self.client.get("/_notifications/send_todays_digest")
      self.assertEqual(self._get_notifications().count(), 0)

      request1 = Request.query.get(requests["Request 1"].id)
      # start and finish request 1
      self.api_helper.modify_object(request1,
                                    {"status": Request.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(request1, {"status": Request.DONE_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      # decline request 1
      self.api_helper.modify_object(request1,
                                    {"status": Request.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 1)
      self.api_helper.modify_object(request1, {"status": Request.DONE_STATE})
      self.assertEqual(self._get_notifications().count(), 1)
      # decline request 1 the second time
      self.api_helper.modify_object(request1,
                                    {"status": Request.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 1)

      request6 = Request.query.get(requests["Request 6"].id)
      # start and finish request 6
      self.api_helper.modify_object(request6,
                                    {"status": Request.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 1)
      self.api_helper.modify_object(request6, {"status": Request.DONE_STATE})
      self.assertEqual(self._get_notifications().count(), 1)
      # decline request 6
      self.api_helper.modify_object(request6,
                                    {"status": Request.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 2)

      # send all notifications
      self.client.get("/_notifications/send_todays_digest")
      self.assertEqual(self._get_notifications().count(), 0)

      # Refresh the object because of the lost session due to the get call.
      request6 = Request.query.get(requests["Request 6"].id)
      self.api_helper.modify_object(request6,
                                    {"status": Request.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(request6,
                                    {"status": Request.DONE_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(request6,
                                    {"status": Request.VERIFIED_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(request6,
                                    {"status": Request.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      # decline request 6
      self.api_helper.modify_object(request6, {"status": Request.DONE_STATE})
      self.assertEqual(self._get_notifications().count(), 0)
      self.api_helper.modify_object(request6,
                                    {"status": Request.PROGRESS_STATE})
      self.assertEqual(self._get_notifications().count(), 1)
