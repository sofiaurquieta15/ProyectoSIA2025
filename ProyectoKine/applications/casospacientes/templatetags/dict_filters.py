from django import template

register = template.Library()

@register.filter
def dict_get(dict_data, key):
    try:
        return dict_data.get(int(key)) or dict_data.get(str(key))
    except:
        return ""