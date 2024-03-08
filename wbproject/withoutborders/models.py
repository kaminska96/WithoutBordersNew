from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Profile(models.Model):
    first_name = models.TextField()
    last_name = models.TextField()
    # organization_name = models.TextField(blank = True)
    username = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username
