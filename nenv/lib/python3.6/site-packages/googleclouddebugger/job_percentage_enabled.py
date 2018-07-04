"""Determine if the debugger should be enabled.
"""

from borg.borgletlib.python import pyborgletinfo
from chubby.python.public import pywrapbns_basic
from pyglib import logging


def IsPercentageEnabled(percent_enabled):
  """Returns true if the task is running in borg and should is enabled."""

  if percent_enabled >= 100:
    return True

  if percent_enabled <= 0:
    return False

  if not pyborgletinfo.RunningUnderBorglet():
    return True

  task_info = pyborgletinfo.GetExtendedTaskInfo(0)
  task_bns = task_info.bns_name

  # task_bns has the form
  # /bns/<cell>/borg/<cell>/bns/<username>/<jobname>/<task_num>
  # The trailing <task_num> needs to be dropped
  last_slash_index = task_bns.rfind('/')
  if last_slash_index < 0:
    logging.error('Could not parse task BNS: %s', task_bns)
    return False

  # get the task count
  job_bns = task_bns[:last_slash_index]
  task_count = pywrapbns_basic.BNSBasic.NumTasks(job_bns)
  if task_count <= 0:
    return False
  return percent_enabled >= ((task_info.task_id + 1) * 100 / task_count)

