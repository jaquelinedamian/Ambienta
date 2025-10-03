from django import template

register = template.Library()

@register.filter(name='percentage')
def percentage(value):
    """Converte um decimal para porcentagem."""
    try:
        return int(float(value) * 100)
    except (ValueError, TypeError):
        return 0