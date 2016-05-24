# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

from integration.ggrc import TestCase


class TestBasicCsvImport(TestCase):

  def setUp(self):
    TestCase.setUp(self)
    self.client.get("/login")

  def test_policy_basic_import(self):
    filename = "ca_setup_for_deletion.csv"
    self.import_file(filename)

    filename = "ca_deletion.csv"
    response_data_dry = self.import_file(filename, dry_run=True)
    response_data = self.import_file(filename)
    self.assertEqual(response_data_dry, response_data)

    self.assertEqual(response_data[0]["deleted"], 2)
    self.assertEqual(response_data[0]["ignored"], 0)
