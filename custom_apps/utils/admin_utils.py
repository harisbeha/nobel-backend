def run_safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except:
        pass


def generate_field_getter(selector, name, admin_order_field=None, preprocessor=None):
    selector_parts = selector.split('.')

    def getter(obj):
        parent = obj
        for part in selector_parts:
            parent = getattr(parent, part, None)
            if not parent:
                break
        value = parent
        if preprocessor:
            value = run_safe(preprocessor, value) or value
        return value

    getter.short_description = name
    getter.admin_order_field = admin_order_field or selector_parts[0]
    return getter
