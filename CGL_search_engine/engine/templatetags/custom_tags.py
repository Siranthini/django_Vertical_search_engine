from django import template

register = template.Library()

@register.filter
def get_item(original_data, index):
    # Assuming 'original_data' is a DataFrame with the appropriate structure
    try:
        return original_data.iloc[index].to_dict()
    except IndexError:
        return None