from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    goal = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)  # New field

    def __str__(self):
        return self.user.username

    def get_host_rating(self):
        ratings = Rating.objects.filter(hobby__host=self.user)
        return ratings.aggregate(Avg('score'))['score__avg'] or 0

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Hobby(models.Model):
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_hobbies')
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='hobby_images/', blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    tags = models.ManyToManyField(Tag, blank=True)
    max_participants = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    date = models.DateTimeField(null=True, blank=True)  # <-- Add this line
    place = models.CharField(max_length=255, blank=True)  # <-- Add this line

    def __str__(self):
        return self.title

    def get_average_rating(self):
        return self.ratings.aggregate(Avg('score'))['score__avg'] or 0

    def get_participant_count(self):
        return self.applications.filter(status='accepted').count()

class Application(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')]

    hobby = models.ForeignKey(Hobby, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('hobby', 'applicant')

class Rating(models.Model):
    hobby = models.ForeignKey(Hobby, on_delete=models.CASCADE, related_name='ratings')
    rater = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])

    class Meta:
        unique_together = ('hobby', 'rater')

class ParticipantRating(models.Model):
    hobby = models.ForeignKey(Hobby, on_delete=models.CASCADE)
    participant = models.ForeignKey(User, on_delete=models.CASCADE)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='host_ratings')
    score = models.PositiveIntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])
    rated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('hobby', 'participant')