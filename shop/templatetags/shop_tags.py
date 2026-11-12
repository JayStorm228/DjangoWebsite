from django import template

register = template.Library()


@register.filter
def ru_plural(value, forms: str) -> str:
    """Русская плюрализация: {{ n|ru_plural:"курс,курса,курсов" }}."""
    try:
        number = abs(int(value))
    except (TypeError, ValueError):
        return forms.split(",")[0]

    one, few, many = (forms.split(",") + ["", "", ""])[:3]
    if number % 10 == 1 and number % 100 != 11:
        return one
    if 2 <= number % 10 <= 4 and not 12 <= number % 100 <= 14:
        return few
    return many
