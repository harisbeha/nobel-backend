from enum import Enum


class ChoiceEnum(Enum):
    @classmethod
    def choices(cls):
        return tuple((x.name, x.value) for x in cls)


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
