from core.models import Message


def unread_notifications(request):
    """Add unread notifications count to all templates."""
    if request.user.is_authenticated:
        unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()
        return {'unread_notifications_count': unread_count}
    return {'unread_notifications_count': 0}
