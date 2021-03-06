# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: jernej@reciprocitylabs.com
# Maintained By: jernej@reciprocitylabs.com

"""PyTest fixtures"""

import pytest   # pylint: disable=import-error

from lib import base
from lib import conftest_utils
from lib.constants.test import batch


@pytest.yield_fixture(scope="session")
def db_drop():
  """Reset the DB"""
  # todo
  pass


@pytest.yield_fixture(scope="session")
def db_migrate():
  """Make sure the DB is up to date"""
  # todo
  pass


@pytest.yield_fixture(scope="class")
def selenium():
  """Setup test resources for running test in headless mode.

  Returns:
      base.CustomDriver
  """
  selenium_base = base.Selenium()
  yield selenium_base
  selenium_base.close_resources()


@pytest.yield_fixture(scope="class")
def custom_program_attribute(selenium):
  """Creates a custom attribute for a program object"""
  # pylint: disable=redefined-outer-name
  cust_attr_widget = conftest_utils.create_custom_program_attribute(
      selenium.driver)
  yield cust_attr_widget
  # todo: delete this custom attribute


@pytest.yield_fixture(scope="class")
def new_control(selenium):
  """Creates a new control object.

  Returns:
      lib.page.modal.new_program.NewControlModal
  """
  control_info_page = conftest_utils.lhn_create_control(selenium.driver)
  yield control_info_page
  selenium.driver.get(control_info_page.url)
  conftest_utils.delete_control(selenium.driver)


@pytest.yield_fixture(scope="class")
def new_program(selenium, new_control):
  """Creates a new program object.

  Returns:
      lib.page.modal.new_program.NewProgramModal
  """
  # pylint: disable=redefined-outer-name
  modal, program_info_page = conftest_utils.lhn_create_program(selenium.driver)
  yield modal, program_info_page
  selenium.driver.get(program_info_page.url)
  conftest_utils.delete_program(selenium.driver)


@pytest.yield_fixture(scope="class")
def new_org_group(selenium):
  """Creates a new org group object.

  Returns:
      lib.page.modal.new_program.NewOrgGroupModal
  """
  org_group_page = conftest_utils.lhn_create_org_group(selenium.driver)
  yield org_group_page
  selenium.driver.get(org_group_page.url)
  conftest_utils.delete_org_group(selenium.driver)


@pytest.yield_fixture(scope="class")
def new_risk(selenium):
  """Creates a new risk group object.

  Returns:
      lib.page.modal.new_program.NewOrgGroupModal
  """
  risk_page = conftest_utils.lhn_create_risk(selenium.driver)
  yield risk_page
  selenium.driver.get(risk_page.url)
  conftest_utils.delete_risk(selenium.driver)


@pytest.yield_fixture(scope="class")
def battery_of_controls(selenium):
  """Creates 3 control objects"""
  controls = []

  for _ in xrange(batch.BATTERY):
    controls.append(conftest_utils.lhn_create_control(selenium.driver))

  yield controls
