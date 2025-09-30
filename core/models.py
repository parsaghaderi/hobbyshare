import os, uuid
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image # Make sure PIL/Pillow is installed
from django.dispatch import receiver

def profile_image_upload_to(instance, filename): #check later!!!
    base, ext = os.path.splitext(filename)
    ext = (ext or '.jpg').lower()
    ts = timezone.now().strftime('%Y%m%d%H%M%S')
    return f'profile_pics/{instance.user_id}/{ts}_{uuid.uuid4().hex}{ext}'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    goal = models.CharField(max_length=255, blank=True)
    # This is the simple, correct way, just like your Hobby model.
    image = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} Profile'

    # The custom save method has been removed to prevent file handling errors.
    # Django and the database will handle saving the image path directly.

    def get_host_rating(self):
        ratings = Rating.objects.filter(hobby__host=self.user)
        return ratings.aggregate(Avg('score'))['score__avg'] or 0

    def get_average_rating(self):
        # alias used by templates
        return self.get_host_rating()

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
    image = models.ImageField(upload_to='hobby_images/', null=True, blank=True)  # added
    max_participants = models.PositiveIntegerField(default=10)
    date = models.DateTimeField()
    place = models.CharField(max_length=300)
    province = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    neighbourhood = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def has_ended(self):
        return bool(self.date and timezone.now() > self.date)

    def user_is_accepted(self, user):
        return self.applications.filter(applicant=user, status='accepted').exists()

    def get_average_rating(self):
        return self.ratings.aggregate(Avg('score'))['score__avg'] or 0

    def get_participant_count(self):
        return self.applications.filter(status='accepted').count()

    def category_name(self):
        return self.category.name if self.category else "Uncategorized"


class Requirement(models.Model):
    hobby = models.ForeignKey(Hobby, on_delete=models.CASCADE, related_name='requirements', null=True)
    name = models.CharField(max_length=255)
    provided_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='provided_requirements')
    suggested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='suggested_requirements')
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # New optional classification to enable supplier matching
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True, related_name='requirements')
    tag = models.ForeignKey('Tag', on_delete=models.SET_NULL, null=True, blank=True, related_name='requirements')
    # Supplier linkage
    supplier_item = models.ForeignKey('SupplierItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='requirements')
    supplier_status = models.CharField(max_length=10, choices=[('pending','Pending'),('accepted','Accepted'),('declined','Declined')], default='pending')
    supplier_requested_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        hobby_title = self.hobby.title if self.hobby else 'No hobby'
        return f"{self.name} for {hobby_title}"

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
    anonymous = models.BooleanField(default=True)
    comment = models.TextField(blank=True)

    class Meta:
        unique_together = ('hobby', 'rater')

class ParticipantRating(models.Model):
    hobby = models.ForeignKey(Hobby, on_delete=models.CASCADE)
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    score = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)

    class Meta:
        unique_together = ('hobby', 'host', 'participant')

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# This signal is redundant and causes a recursion error. It must be removed.
# @receiver(post_save, sender=User)
# def save_user_profile(sender, instance, **kwargs):
#     instance.profile.save()

# Suppliers
def supplier_item_image_upload(instance, filename):
    base, ext = os.path.splitext(filename)
    ext = (ext or '.jpg').lower()
    ts = timezone.now().strftime('%Y%m%d%H%M%S')
    return f'supplier_items/{instance.supplier.user_id}/{ts}_{uuid.uuid4().hex}{ext}'

class Supplier(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='supplier')
    province = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    neighbourhood = models.CharField(max_length=150, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Supplier {self.user.username}'

class SupplierItem(models.Model):
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='supplier_items')
    tag = models.ForeignKey(Tag, on_delete=models.SET_NULL, null=True, blank=True, related_name='supplier_items')
    quantity = models.PositiveIntegerField(default=1)
    is_rental = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to=supplier_item_image_upload, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name} ({self.supplier.user.username})'