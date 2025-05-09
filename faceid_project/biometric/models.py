from django.db import models
from django.contrib.auth.models import User
import numpy as np

class FaceEncoding(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    encoding = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='face_images/', null=True, blank=True)

    def set_encoding(self, encoding):
        if isinstance(encoding, np.ndarray):
            self.encoding = encoding.tobytes().hex()
        else:
            raise ValueError("Encoding must be a NumPy array")

    def get_encoding(self):
        if self.encoding:
            return np.frombuffer(bytes.fromhex(self.encoding))
        return None

class DiaryEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diary_entries')
    title = models.CharField(max_length=200)
    content = models.TextField()
    photo = models.ImageField(upload_to='diary_photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.user.username}"