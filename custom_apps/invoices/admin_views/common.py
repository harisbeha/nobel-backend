class ReadOnlyMixin(object):
    def get_readonly_fields(self, request, obj=None):
        return self.model._meta.fields

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
