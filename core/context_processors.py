from .models import Notification

def notifications_context(request):
    """Add unread notifications count to all templates"""
    context = {}
    if request.user.is_authenticated:
        context['unread_notifications_count'] = Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
    return context