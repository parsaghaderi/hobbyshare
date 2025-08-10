from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    goal = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='profile_pics/', default='default.jpg', blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'

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
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True)
    max_participants = models.PositiveIntegerField(default=10)
    date = models.DateTimeField()
    place = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def get_average_rating(self):
        return self.ratings.aggregate(Avg('score'))['score__avg'] or 0

    def get_participant_count(self):
        return self.applications.filter(status='accepted').count()


class Requirement(models.Model):
    hobby = models.ForeignKey(Hobby, on_delete=models.CASCADE, related_name='requirements', null=True)
    name = models.CharField(max_length=255)
    provided_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='provided_requirements')

    def __str__(self):
        if self.hobby:
            return f"{self.name} for {self.hobby.title}"
        return f"{self.name} (No associated hobby)"


class Application(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')]

    hobby = models.ForeignKey(Hobby, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('hobby', 'applicant')

    def __str__(self):
        return f'Application by {self.applicant.username} for {self.hobby.title}'

class Rating(models.Model):
    hobby = models.ForeignKey(Hobby, on_delete=models.CASCADE, related_name='ratings')
    rater = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.IntegerField(choices=[(i, i) for i in range(1, 6)])

    class Meta:
        unique_together = ('hobby', 'rater')

class ParticipantRating(models.Model):
    hobby = models.ForeignKey(Hobby, on_delete=models.CASCADE)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    score = models.IntegerField(choices=[(i, i) for i in range(1, 6)])

    class Meta:
        unique_together = ('hobby', 'host', 'participant')

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()