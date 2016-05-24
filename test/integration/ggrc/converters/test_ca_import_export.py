# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

"""Test import and export of objects with custom attributes."""

from flask.json import dumps

from integration.ggrc import TestCase
from integration.ggrc.generator import ObjectGenerator
from ggrc.models import AccessGroup
from ggrc.models import Product


class TestCustomAttributeImportExport(TestCase):
  """Test import and export with custom attributes."""

  def setUp(self):
    """Setup stage for each test.

    Generate all required objects and custom attributes for import of csvs
    containing custom attributes. This stage also initializes a http client
    that is used for sending import/export requests.
    """
    TestCase.setUp(self)
    self.generator = ObjectGenerator()
    self.create_custom_attributes()
    self.create_people()
    self.client.get("/login")
    self.headers = {
        'Content-Type': 'application/json',
        "X-Requested-By": "gGRC",
        "X-export-view": "blocks",
    }

  def create_custom_attributes(self):
    """Generate custom attributes needed for csv import

    This function generates all custom attributes on Product and Access Group,
    that are used in product_with_all_custom_attributes.csv and
    multi_word_object_custom_attribute_test.csv files.
    """
    gen = self.generator.generate_custom_attribute
    gen("product", attribute_type="Text", title="normal text")
    gen("product", attribute_type="Text", title="man text", mandatory=True)
    gen("product", attribute_type="Rich Text", title="normal RT")
    gen("product", attribute_type="Rich Text", title="man RT", mandatory=True)
    gen("product", attribute_type="Date", title="normal Date")
    gen("product", attribute_type="Date", title="man Date", mandatory=True)
    gen("product", attribute_type="Checkbox", title="normal CH")
    gen("product", attribute_type="Checkbox", title="man CH", mandatory=True)
    gen("product", attribute_type="Dropdown", title="normal select",
        options="a,b,c,d")
    gen("product", attribute_type="Dropdown", title="man select",
        options="e,f,g", mandatory=True)
    gen("product", attribute_type="Map:Person", title="normal person")
    gen("product", attribute_type="Map:Person", title="man person",
        mandatory=True)

    gen("access_group", attribute_type="Text",
        title="access group test custom", mandatory=True)

  def create_people(self):
    """Create people used in the csv files.

    This function should be removed and people should be added into the csv
    file as a Person block.
    """
    emails = [
        "user1@ggrc.com",
        "miha@policy.com",
        "someone.else@ggrc.com",
        "another@user.com",
    ]
    for email in emails:
      self.generator.generate_person({
          "name": email.split("@")[0].title(),
          "email": email,
      }, "gGRC Admin")

  def test_product_ca_import(self):
    """Test import of product with all custom attributes.

    This tests covers all possible custom attributes with mandatory flag turned
    off and on, and checks for all warnings that should be present.
    """
    filename = "product_with_all_custom_attributes.csv"
    response = self.import_file(filename)[0]
    expected_warnings = {
        "Line 6: man CH contains invalid data. The value will be ignored.",
        "Line 8: normal select contains invalid data. The value will be"
        " ignored.",
        "Line 10: man select contains invalid data. The value will be"
        " ignored.",
        "Line 11: normal CH contains invalid data. The value will be ignored.",
        "Line 12: man CH contains invalid data. The value will be ignored.",
        "Line 14: normal Date contains invalid data. The value will be"
        " ignored.",
        "Line 16: man Date contains invalid data. The value will be ignored.",
        "Line 21: Owner field does not contain a valid owner. You will be"
        " assigned as object owner.",
        "Line 22: Specified user 'kr@en.com' does not exist. That user will be"
        " ignored.",
        "Line 22: Owner field does not contain a valid owner. You will be"
        " assigned as object owner.",
        "Line 26: Owner field does not contain a valid owner. You will be"
        " assigned as object owner.",
        "Line 27: Specified user 'user@exameuple.com' does not exist. That"
        " user will be ignored.",
        "Line 27: Owner field does not contain a valid owner. You will be"
        " assigned as object owner."
    }

    expected_errors = {
        "Line 6: Field man CH is required. The line will be ignored.",
        "Line 9: Field man select is required. The line will be ignored.",
        "Line 10: Field man select is required. The line will be ignored.",
        "Line 12: Field man CH is required. The line will be ignored.",
        "Line 16: Field man Date is required. The line will be ignored.",
        "Line 18: Field man RT is required. The line will be ignored.",
        "Line 20: Field man text is required. The line will be ignored.",
        "Line 21: Field man person is required. The line will be ignored.",
        "Line 28: Field Title is required. The line will be ignored."
    }

    self.assertEqual(expected_warnings, set(response["row_warnings"]))
    self.assertEqual(expected_errors, set(response["row_errors"]))
    self.assertEqual(17, response["created"])
    self.assertEqual(9, response["ignored"])
    self.assertEqual(17, Product.query.count())

  def tests_ca_export(self):
    """Test exporting products with custom attributes

    This test checks that we get a propper response when exporting objects with
    custom attributes and that the response data actually contains more lines
    than an empty template would.
    This tests relys on the import tests to work. If those fail they need to be
    fixied before this one.
    """
    filename = "product_with_all_custom_attributes.csv"
    self.import_file(filename)

    data = [{
        "object_name": "Product",
        "filters": {
            "expression": {},
        },
        "fields": "all",
    }]
    response = self.client.post("/_service/export_csv", data=dumps(data),
                                headers=self.headers)

    self.assert200(response)
    self.assertEqual(len(response.data.splitlines()), 21)

  def test_multi_word_object_with_ca(self):
    """Test multi-word (e.g. Access Group, Data Asset) object import"""
    filename = "multi_word_object_custom_attribute_test.csv"
    response = self.import_file(filename)[0]
    self.assertEqual([], response["row_warnings"])
    self.assertEqual([], response["row_errors"])
    self.assertEqual(10, response["created"])
    self.assertEqual(0, response["ignored"])
    self.assertEqual(0, response["updated"])
    self.assertEqual(10, AccessGroup.query.count())

    for id_ in range(1, 11):
      access_group = AccessGroup.query.filter(
          AccessGroup.slug == "ag-{}".format(id_)).first()
      filtered = [val for val in access_group.custom_attribute_values if
                  val.attribute_value == "some text {}".format(id_)]
      self.assertEqual(len(filtered), 1)
