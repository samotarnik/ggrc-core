# Copyright (C) 2015 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: jernej@reciprocitylabs.com
# Maintained By: jernej@reciprocitylabs.com


class ElementNotFound(Exception):
  """Raised when an element is not found. Selenium has it's own exception but
  when we're iterating through multiple elements and expect one, we raise our
  own.
  """


class DocstringsMissing(Exception):
  """Since we require for certain classes to have docstrings, we raise this
  exception in case the methods are missing them.
  """


class ElementMovingTimeout(Exception):
  """When trying to detect if an element stopped moving so it receives the
  click, we usually have a timeout for that. If the timeout is reached, this
  exception is raised.
  """


class RedirectTimeout(Exception):
  """When detecting if a redirect has occured, we usually check that the
  loop isn't infinite and raise this exception if the timeout is reached.
  """
