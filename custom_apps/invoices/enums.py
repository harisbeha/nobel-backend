from enum import Enum


class ChoiceEnum(Enum):
    @classmethod
    def choices(cls):
        return tuple((x.value, x.name) for x in cls)

    @classmethod
    def text_name(cls, value):
        try:
            return next(x.name for x in cls if x.value == value)
        except StopIteration:
            raise KeyError(value)

    @classmethod
    def human_name(cls, value):
        inhuman = cls.text_name(value)
        lowercase = ' '.join(x.lower() for x in inhuman.split('_'))
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


class BuildingType(ChoiceEnum):
    STANDALONE = 1
    MIXED_USE = 2


class SnowStatus(ChoiceEnum):
    NONE = 0
    NEEDS_STACKING = 1
    NEEDS_HAULING = 2


class Group(ChoiceEnum):
    PROVIDER = 'Provider'
    CLIENT_INVOICE_ADMIN = 'Client Invoice Administrator'
    REGIONAL_MANAGER = 'Regional Manager'
    SERVICE_PROVIDER = 'Service Provider'
    INTERNAL_STAFF = 'Internal Staff'


WORKFLOW_SPEC = \
    {'initial_state': ReportState.CREATED,
     'spec': {
         ReportState.CREATED:
             {'allowed': {Group.PROVIDER: ['create']}},
         ReportState.INITIALIZED:
             {'allowed': {Group.PROVIDER: ['edit']}},
         ReportState.SAFETY_REVIEWED:
             {'allowed': {Group.REGIONAL_MANAGER: ['close']}},
         ReportState.SAFETY_REVIEW_CLOSED:
             {'allowed': {}},
         ReportState.FORECASTED:
             {'allowed': {Group.INTERNAL_STAFF: ['send']}},
         ReportState.SENT_TO_PROVIDER:
             {'allowed': {Group.INTERNAL_STAFF: ['close']}},
         ReportState.VALIDATED:
             {'allowed': {Group.INTERNAL_STAFF: ['close']}},
         ReportState.FINALIZED:
             {'allowed': {}},
     }}
