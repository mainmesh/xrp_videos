from django.db import models
from django.contrib.auth.models import User


class Message(models.Model):
    """Admin-User messaging and notification system."""
    MESSAGE_TYPES = (
        ('reward', 'Reward'),
        ('withdrawal', 'Withdrawal'),
        ('message', 'Message'),
        ('admin', 'Admin Message'),
    )
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', null=True, blank=True)
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200, blank=True, default='')
    message = models.TextField(blank=True, default='')
    
    # New fields for notification system
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='message')
    content = models.TextField(blank=True, default='')
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        if self.sender:
            return f"{self.sender.username} → {self.receiver.username}: {self.subject or self.content[:50]}"
        return f"Notification → {self.receiver.username}: {self.content[:50]}"


class ChatMessage(models.Model):
    """AI Chatbot conversation history."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages', null=True, blank=True)
    session_id = models.CharField(max_length=100, help_text="For anonymous users")
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Chat at {self.created_at}"


class Announcement(models.Model):
    """Site-wide announcements from admin."""
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
