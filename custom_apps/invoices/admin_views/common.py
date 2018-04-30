class ReadOnlyMixin(object):
    def __init__(self, *args, **kwargs):
        super(ReadOnlyMixin, self).__init__(*args, **kwargs)
        self.readonly_fields = self.model._meta.get_all_field_names()

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class AppendOnlyMixin(object):
    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return []
        return self.model._meta.fields

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        if obj is None:
            return True
        return False
