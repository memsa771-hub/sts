from django import template

register = template.Library()


def _safe_user_display(user, default="Not assigned"):
    if not user:
        return default
    full = user.get_full_name().strip()
    return full or user.username or default


@register.filter(name='user_display')
def user_display(user, default="Not assigned"):
    """Safely show a user's name even when the user is None."""
    return _safe_user_display(user, default)


@register.filter(name='user_initials')
def user_initials(user, default="?"):
    """Safely show user initials even when the user is None."""
    if not user:
        return default
    first = (user.first_name or '').strip()
    last = (user.last_name or '').strip()
    if first and last:
        return f"{first[0]}{last[0]}".upper()
    if first:
        return first[0].upper()
    if user.username:
        return user.username[0].upper()
    return default

@register.filter(name='split')
def split_filter(value, arg):
    """
    Splits a string by the given separator and returns the resulting list
    
    Usage: {{ value|split:"separator" }}
    """
    return value.split(arg)

@register.filter(name='addclass')
def addclass(field, css_classes):
    """
    Add CSS classes to a form field while preserving any existing classes
    
    Usage: {{ form.field|addclass:"class-name another-class" }}
    """
    if hasattr(field, 'as_widget'):
        # Get existing attributes
        attrs = {}
        if hasattr(field.field.widget, 'attrs'):
            attrs = field.field.widget.attrs.copy()
        
        # Combine existing classes with new ones
        existing_classes = attrs.get('class', '')
        if existing_classes:
            classes = f"{existing_classes} {css_classes}"
        else:
            classes = css_classes
            
        attrs['class'] = classes
        return field.as_widget(attrs=attrs)
    return field