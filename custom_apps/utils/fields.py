from django.db import models
from jsonfield import JSONField


# noinspection PyPep8Naming
def AddressField(fullname, **kwargs):
    return models.TextField(fullname, max_length=500, **kwargs)


# noinspection PyPep8Naming
def DollarsField(fullname, **kwargs):
    return models.DecimalField(fullname, max_digits=8, decimal_places=2, **kwargs)


class AddressMetadataStorageMixin(models.Model):
    class Meta:
        abstract = True

    address_info_storage = JSONField(blank=True, null=True)
