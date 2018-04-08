from django.contrib import humanize
from enum import Enum


class ChoiceEnum(Enum):
    @classmethod
    def choices(cls):
        return tuple((x.value, x.name) for x in cls)

    @classmethod
    def name(cls, value):
        try:
            return next(x.name for x in cls if x.value == value)
        except StopIteration:
            raise KeyError(value)

    @classmethod
    def human_name(cls, value):
        inhuman = cls.name(value)
        lowercase =' '.join(x.lower() for x in inhuman.split('_'))
        return lowercase[0].upper() + lowercase[1:]

class ReportState(ChoiceEnum):
    CREATED = 1
    INITIALIZED = 2
    SAFETY_REVIEWED = 3
    SAFETY_REVIEW_CLOSED = 4
    PRELIM_GENERATED = 5
    PRE_FORECAST_REVIEWED = 6
    FORECASTED = 7
    SENT_TO_PROVIDER = 8
    VALIDATED = 9
    FINALIZED = 10

    REJECTED = -1
