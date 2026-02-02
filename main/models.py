from datetime import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    USER_CHOISE = (
        ('admin','admin'),
        ('agent','agent'),
        ('client','client'),
    )

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(null=True, blank=True, unique=True)
    phone = models.CharField(max_length=13, null=True, blank=True, unique=True)
    image = models.ImageField(upload_to='user_images', null=True, blank=True)
    role = models.CharField(max_length=15, choices=USER_CHOISE, null=True, blank=True)
    is_confirmation = models.BooleanField(default=False)
    confirmation_code = models.CharField(max_length=5, null=True, blank=True)
    firebase_token = models.CharField(max_length=500, null=True, blank=True)


class Balans(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="balans")
    balans = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.user.username} - {self.balans}"


class ChatRoom(models.Model):
    property = models.ForeignKey(
        'product.Property', on_delete=models.CASCADE, related_name="chat_rooms"
    ,null=True, blank=True)
    user_1 = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="chat_user1"
    )
    user_2 = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="chat_user2"
    )
    owner = models.ForeignKey( 
        CustomUser, on_delete=models.CASCADE, related_name="owned_chats"
    )
    
    room_name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user_1", "user_2", ], name="unique_chat_between_users"
            )
        ]

    def save(self, *args, **kwargs):
        # user_1 va user_2 tartibini kafolatlash (masalan, doim kichik id birinchi)
        if self.user_1.id > self.user_2.id:
            self.user_1, self.user_2 = self.user_2, self.user_1
        ids = sorted([self.user_1.id, self.user_2.id])
        self.room_name = f"chat_{ids[0]}_{ids[1]}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Chat between {self.user_1} and {self.user_2}"


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="sent_messages"
    )
    content = models.TextField(blank=True, null=True)
    # image = models.ImageField(upload_to="chat_images/", blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    flowed = models.BooleanField(default=False)
    def __str__(self):
        return f"Message from {self.sender} in {self.room}"