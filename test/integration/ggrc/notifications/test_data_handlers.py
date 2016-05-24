# Copyright (C) 2016 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

"""Tests for notifications for models with assignable mixin."""

from sqlalchemy import and_

from ggrc import db
from ggrc import contributions
from ggrc.models import Notification
from ggrc.models import NotificationType
from ggrc.models import Request
from integration.ggrc import api_helper
from integration.ggrc import TestCase
from integration.ggrc import generator


class TestRequestDataHandlers(TestCase):
  """Test data handlers for various request notifications."""

  def setUp(self):
    TestCase.setUp(self)
    self.client.get("/login")
    self.api_helper = api_helper.Api()
    self.import_file("request_full_no_warnings.csv")
    self.request1 = Request.query.filter_by(slug="Request 1").one()
    self.request3 = Request.query.filter_by(slug="Request 3").one()
    self.generator = generator.ObjectGenerator()
    self.handlers = contributions.contributed_notifications()

  def _call_notif_handler(self, notif):
    """Call the default data handler for the notification object.

    Args:
      notif (Notification): notification for which we want te get data

    Returns:
      Result of the data handler for the given object.
    """
    return self.handlers[notif.object_type](notif)

  @classmethod
  def _get_notification(cls, obj, notif_type):
    return db.session.query(Notification).join(NotificationType).filter(and_(
        Notification.object_id == obj.id,
        Notification.object_type == obj.type,
        NotificationType.name == notif_type,
    ))

  def test_open_request(self):
    """Test data handlers for opened requests."""
    notif = self._get_notification(self.request1, "request_open").first()
    open_data = self._call_notif_handler(notif)
    request_1_expected_keys = set([
        "user1@a.com",
        "user2@a.com",
        "user3@a.com",
        "user4@a.com",
        "user5@a.com",
    ])

    self.assertEqual(set(open_data.keys()), request_1_expected_keys)

    notif = self._get_notification(self.request3, "request_open").first()
    open_data = self._call_notif_handler(notif)
    request_3_expected_keys = set([
        "user1@a.com",
        "user2@a.com",
        "user@example.com",
    ])

    self.assertEqual(set(open_data.keys()), request_3_expected_keys)

  def test_declined_request(self):
    """Test data handlers for declined requests"""

    # decline request 1
    request1 = Request.query.filter_by(slug="Request 1").first()
    self.api_helper.modify_object(request1, {"status": Request.DONE_STATE})
    self.api_helper.modify_object(request1, {"status": Request.PROGRESS_STATE})

    notif = self._get_notification(self.request1, "request_declined").first()
    declined_data = self._call_notif_handler(notif)
    requester_emails = set([
        "user2@a.com",
        "user3@a.com",
    ])

    self.assertEqual(set(declined_data.keys()), requester_emails)

  def test_request_comments(self):
    request1 = Request.query.filter_by(slug="Request 1").first()
    _, comment = self.generator.generate_comment(
        request1, "Verifier", "some comment", send_notification="true")

    notif = self._get_notification(comment, "comment_created").first()

    declined_data = self._call_notif_handler(notif)
    requester_emails = set([
        "user2@a.com",
        "user3@a.com",
        "user4@a.com",
        "user5@a.com",
    ])

    self.assertEqual(set(declined_data.keys()), requester_emails)
