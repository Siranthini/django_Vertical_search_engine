from django import template
import pandas as pd

register = template.Library()

@register.filter

def get_item(dictionary, key):
    return dictionary.get(key)


def get_value_by_index(dataframe, index):
    if isinstance(dataframe, pd.DataFrame) and index in dataframe.index:
        row = dataframe.loc[index].to_dict()
        return row
    return None

@register.filter
def zip_lists(list1, list2):
    return zip(list1, list2)