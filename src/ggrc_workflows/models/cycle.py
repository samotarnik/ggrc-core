# Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Module contains a workflow Cycle model
"""

from sqlalchemy import orm

from ggrc import db
from ggrc.models.mixins import Described
from ggrc.models.mixins import Slugged
from ggrc.models.mixins import Stateful
from ggrc.models.mixins import Timeboxed
from ggrc.models.mixins import Titled
from ggrc.models.mixins import WithContact


class Cycle(WithContact, Stateful, Timeboxed, Described, Titled, Slugged,
            db.Model):
  """Workflow Cycle model
  """
  __tablename__ = 'cycles'
  _title_uniqueness = False

  VALID_STATES = (u'Assigned', u'InProgress', u'Finished', u'Verified')

  workflow_id = db.Column(
      db.Integer, db.ForeignKey('workflows.id'), nullable=False)
  cycle_task_groups = db.relationship(
      'CycleTaskGroup', backref='cycle', cascade='all, delete-orphan')
  cycle_task_group_objects = db.relationship(
      'CycleTaskGroupObject', backref='cycle', cascade='all, delete-orphan')
  cycle_task_group_object_tasks = db.relationship(
      'CycleTaskGroupObjectTask', backref='cycle',
      cascade='all, delete-orphan')
  cycle_task_entries = db.relationship(
      'CycleTaskEntry', backref='cycle', cascade='all, delete-orphan')
  is_current = db.Column(db.Boolean, default=True, nullable=False)
  next_due_date = db.Column(db.Date)

  @property
  def cycle_task_group_object_objects_for_cache(self):
    """Changing Cycle state must invalidate `workflow_state` on objects
    """
    return [
        (o.object_type, o.object_id) for o in self.cycle_task_group_objects]

  _publish_attrs = [
      'workflow',
      'cycle_task_groups',
      'is_current',
      'next_due_date',
  ]

  _aliases = {
      "cycle_workflow": {
          "display_name": "Workflow",
          "filter_by": "_filter_by_cycle_workflow",
      },
  }

  @classmethod
  def _filter_by_cycle_workflow(cls, predicate):
    from ggrc_workflows.models.workflow import Workflow
    return Workflow.query.filter(
        (Workflow.id == cls.workflow_id) &
        (predicate(Workflow.slug) | predicate(Workflow.title))
    ).exists()

  @classmethod
  def eager_query(cls):
    """Add cycle task groups to cycle eager query

    This function adds cycle_task_groups as a join option when fetching cycles,
    and makes sure we fetch all cycle related data needed for generating cycle
    json, in one query.

    Returns:
      a query object with cycle_task_groups added to joined load options.
    """
    query = super(Cycle, cls).eager_query()
    return query.options(
        orm.joinedload('cycle_task_groups'),
    )
