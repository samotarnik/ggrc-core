# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: miha@reciprocitylabs.com
# Maintained By: miha@reciprocitylabs.com

"""Tests for workflow object exports."""

from os.path import abspath
from os.path import dirname
from os.path import join
from os.path import normpath
from flask.json import dumps

from ggrc.app import app
from ggrc_workflows.models import Workflow
from integration.ggrc import TestCase
from integration.ggrc_workflows.generator import WorkflowsGenerator

THIS_ABS_PATH = abspath(dirname(__file__))
CSV_DIR = normpath(join(THIS_ABS_PATH, '../../../csv_files/ggrc_workflows/'))


class TestExportEmptyTemplate(TestCase):

  """Test empty export for all workflow object types."""

  def setUp(self):
    self.client.get("/login")
    self.headers = {
        'Content-Type': 'application/json',
        "X-Requested-By": "gGRC",
        "X-export-view": "blocks",
    }

  def test_single_object_export(self):
    """Test empty exports for workflow only."""
    data = [{"object_name": "Workflow", "fields": "all"}]

    response = self.client.post("/_service/export_csv",
                                data=dumps(data), headers=self.headers)
    self.assertEqual(response.status_code, 200)
    self.assertIn("Title*", response.data)

  def test_multiple_objects(self):
    """Test empty exports for all workflow object in one query."""
    data = [
        {"object_name": "Workflow", "fields": "all"},
        {"object_name": "TaskGroup", "fields": "all"},
        {"object_name": "TaskGroupTask", "fields": "all"},
        {"object_name": "Cycle", "fields": "all"},
        {"object_name": "CycleTaskGroup", "fields": "all"},
        {"object_name": "CycleTaskGroupObjectTask", "fields": "all"},
    ]

    response = self.client.post("/_service/export_csv",
                                data=dumps(data), headers=self.headers)
    self.assertEqual(response.status_code, 200)
    self.assertIn("Workflow,", response.data)
    self.assertIn("Task Group,", response.data)
    self.assertIn("Task,", response.data)
    self.assertIn("Cycle,", response.data)
    self.assertIn("Cycle Task Group,", response.data)
    self.assertIn("Cycle Task Group Object Task,", response.data)


class TestExportMultipleObjects(TestCase):

  """ Test data is found in the google sheet:
  https://docs.google.com/spreadsheets/d/1Jg8jum2eQfvR3kZNVYbVKizWIGZXvfqv3yQpo2rIiD8/edit#gid=2035742544
  """

  @classmethod
  def setUpClass(cls):  # pylint: disable=C0103
    TestCase.clear_data()
    cls.tc = app.test_client()
    cls.tc.get("/login")
    cls.import_file("workflow_big_sheet.csv")

  @classmethod
  def import_file(cls, filename, dry_run=False):
    data = {"file": (open(join(CSV_DIR, filename)), filename)}
    headers = {
        "X-test-only": "true" if dry_run else "false",
        "X-requested-by": "gGRC",
    }
    cls.tc.post("/_service/import_csv",
                data=data, headers=headers)

  def activate(self):
    """ activate workflows just once after the class has been initialized

    This should be in setUpClass method, but we can't access the server
    context from there."""
    gen = WorkflowsGenerator()

    # generate cycle for the only one time wf
    wf1 = Workflow.query.filter_by(status="Draft", slug="wf-1").first()
    if wf1:
      gen.generate_cycle(wf1)

    workflows = Workflow.query.filter_by(status="Draft").all()
    for wf in workflows:
      gen.activate_workflow(wf)

  def setUp(self):
    self.client.get("/login")
    self.headers = {
        'Content-Type': 'application/json',
        "X-Requested-By": "gGRC",
        "X-export-view": "blocks",
    }
    self.activate()

  def export_csv(self, data):
    response = self.client.post("/_service/export_csv", data=dumps(data),
                                headers=self.headers)
    self.assert200(response)
    return response

  def test_workflow_task_group_mapping(self):
    """ test workflow and task group mappings """
    data = [
        {
            "object_name": "Workflow",  # wf-1
            "filters": {
                "expression": {
                    "op": {"name": "relevant"},
                    "object_name": "TaskGroup",
                    "slugs": ["tg-1"],
                },
            },
            "fields": "all",
        }, {
            "object_name": "TaskGroup",  # tg-1, tg-2
            "filters": {
                "expression": {
                    "op": {"name": "relevant"},
                    "object_name": "__previous__",
                    "ids": ["0"],
                },
            },
            "fields": "all",
        },
    ]
    response = self.export_csv(data).data
    self.assertEqual(3, response.count("wf-1"))  # 1 for wf and 1 on each tg
    self.assertIn("tg-1", response)
    self.assertIn("tg-6", response)

  def test_tg_task(self):
    """ test task group and task mappings """
    data = [
        {
            "object_name": "TaskGroupTask",  # task-1, task-7
            "filters": {
                "expression": {
                    "op": {"name": "relevant"},
                    "object_name": "TaskGroup",
                    "slugs": ["tg-1"],
                },
            },
            "fields": "all",
        }, {
            "object_name": "TaskGroup",  # tg-1, tg-2
            "filters": {
                "expression": {
                    "op": {"name": "relevant"},
                    "object_name": "__previous__",
                    "ids": ["0"],
                },
            },
            "fields": "all",
        },
    ]
    response = self.export_csv(data).data
    self.assertEqual(3, response.count("tg-1"))  # 2 for tasks and 1 for tg
    self.assertIn("task-1", response)
    self.assertIn("task-7", response)

  def test_workflow_cycle_mapping(self):
    """ test workflow and cycle mappings """
    data = [
        {
            "object_name": "Cycle",  # cycle with title wf-1
            "filters": {
                "expression": {
                    "op": {"name": "relevant"},
                    "object_name": "Workflow",
                    "slugs": ["wf-1"],
                },
            },
            "fields": "all",
        }, {
            "object_name": "Workflow",  # wf-1
            "filters": {
                "expression": {
                    "op": {"name": "relevant"},
                    "object_name": "__previous__",
                    "ids": ["0"],
                },
            },
            "fields": "all",
        }, {
            "object_name": "CycleTaskGroup",  # two cycle groups
            "filters": {
                "expression": {
                    "op": {"name": "relevant"},
                    "object_name": "__previous__",
                    "ids": ["0"],
                },
            },
            "fields": "all",
        }, {
            "object_name": "Cycle",  # sholud be same cycle as in first block
            "filters": {
                "expression": {
                    "op": {"name": "relevant"},
                    "object_name": "__previous__",
                    "ids": ["2"],
                },
            },
            "fields": "all",
        }, {
            # Task mapped to any of the two task groups, 3 tasks
            "object_name": "CycleTaskGroupObjectTask",
            "filters": {
                "expression": {
                    "op": {"name": "relevant"},
                    "object_name": "__previous__",
                    "ids": ["2"],
                },
            },
            "fields": "all",
        }, {
            "object_name": "CycleTaskGroup",  # two cycle groups
            "filters": {
                "expression": {
                    "op": {"name": "relevant"},
                    "object_name": "__previous__",
                    "ids": ["4"],
                },
            },
            "fields": "all",
        },
    ]
    response = self.export_csv(data).data
    self.assertEqual(3, response.count("wf-1"))  # 2 for cycles and 1 for wf
    # 3rd block = 2, 5th block = 3, 6th block = 2.
    self.assertEqual(7, response.count("CYCLEGROUP-"))
    self.assertEqual(9, response.count("CYCLE-"))
    self.assertEqual(3, response.count("CYCLETASK-"))

  def test_cycle_taks_objects(self):
    """ test cycle task and various objects """
    data = [
        {
            "object_name": "CycleTaskGroupObjectTask",  #
            "filters": {
                "expression": {
                    "op": {"name": "relevant"},
                    "object_name": "Policy",
                    "slugs": ["p1"],
                },
            },
            "fields": "all",
        }, {
            "object_name": "Policy",  #
            "filters": {
                "expression": {
                    "op": {"name": "relevant"},
                    "object_name": "__previous__",
                    "ids": ["0"],
                },
            },
            "fields": ["slug", "title"],
        },
    ]
    response = self.export_csv(data).data
    self.assertEqual(2, response.count("CYCLETASK-"))
    self.assertEqual(3, response.count(",p1,"))

  def test_workflow_no_access_users(self):
    """ test export of No Access users """
    data = [
        {
            "object_name": "Workflow",
            "fields": ["workflow_mapped"],
            "filters": {
                "expression": {}
            }
        }
    ]
    response = self.export_csv(data).data
    users = response.splitlines()[2:-2]
    expected = [",user20@ggrc.com"] * 10
    self.assertEqual(expected, users)

  def test_wf_indirect_relevant_filters(self):
    """ test related filter for indirect relationships on wf objects """
    def block(obj):
      return {
          "object_name": obj,
          "fields": ["slug"],
          "filters": {
              "expression": {
                  "object_name": "Policy",
                  "op": {"name": "relevant"},
                  "slugs": ["p1"],
              },
          },
      }

    data = [
        block("Workflow"),
        block("Cycle"),
        block("CycleTaskGroup"),
        block("CycleTaskGroupObjectTask"),
    ]
    response = self.export_csv(data).data

    wf = Workflow.query.filter_by(slug="wf-1").first()
    cycle = wf.cycles[0]
    cycle_tasks = []
    for cycle_task in cycle.cycle_task_group_object_tasks:
        is_related = False
        for related_object in cycle_task.related_objects:
            if related_object.slug == "p1":
                is_related = True
        if is_related:
            cycle_tasks.append(cycle_task)

    cycle_task_groups = list({cycle_task.cycle_task_group
                             for cycle_task in cycle_tasks})

    self.assertEqual(1, response.count("wf-"))

    self.assertRegexpMatches(response, ",{}[,\r\n]".format(wf.slug))

    self.assertEqual(1, response.count("CYCLE-"))
    self.assertRegexpMatches(response, ",{}[,\r\n]".format(cycle.slug))

    self.assertEqual(1, response.count("CYCLEGROUP-"))
    self.assertEqual(1, len(cycle_task_groups))
    self.assertRegexpMatches(response, ",{}[,\r\n]".format(
        cycle_task_groups[0].slug))

    self.assertEqual(2, response.count("CYCLETASK-"))
    self.assertEqual(2, len(cycle_tasks))
    for cycle_task in cycle_tasks:
      self.assertRegexpMatches(response, ",{}[,\r\n]".format(
          cycle_task.slug))

    destinations = [
        ("Workflow", wf.slug, 3),
        ("Cycle", cycle.slug, 3),
        ("CycleTaskGroupObjectTask", cycle_tasks[0].slug, 1),
        ("CycleTaskGroupObjectTask", cycle_tasks[1].slug, 1),
    ]
    for object_name, slug, count in destinations:
      data = [{
          "object_name": "Policy",
          "fields": ["slug"],
          "filters": {
              "expression": {
                  "object_name": object_name,
                  "op": {"name": "relevant"},
                  "slugs": [slug],
              },
          },
      }]
      response = self.export_csv(data).data
      self.assertEqual(count, response.count(",p"), "Count for " + object_name)
      self.assertIn(",p1", response)
