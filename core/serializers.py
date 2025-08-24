from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Hobby, Category, Tag, Application, Requirement, Rating, ParticipantRating, Profile, Supplier, SupplierItem

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Profile
        fields = ['user', 'bio', 'goal', 'image']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class RequirementSerializer(serializers.ModelSerializer):
    provided_by = UserSerializer(read_only=True)
    suggested_by = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(source='category', queryset=Category.objects.all(), write_only=True, required=False, allow_null=True)
    tag = TagSerializer(read_only=True)
    tag_id = serializers.PrimaryKeyRelatedField(source='tag', queryset=Tag.objects.all(), write_only=True, required=False, allow_null=True)
    supplier_item_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    supplier_item = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = Requirement
        fields = ['id', 'name', 'provided_by', 'suggested_by', 'is_approved', 'created_at','category','category_id','tag','tag_id','supplier_item','supplier_item_id','supplier_status']

    def get_supplier_item(self, obj):
        if obj.supplier_item:
            return {
                'id': obj.supplier_item.id,
                'name': obj.supplier_item.name,
                'supplier': obj.supplier_item.supplier.user.username,
                'price': str(obj.supplier_item.price),
                'is_rental': obj.supplier_item.is_rental,
                'quantity': obj.supplier_item.quantity,
            }
        return None

class HobbySerializer(serializers.ModelSerializer):
    host = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(source='category', queryset=Category.objects.all(), write_only=True, required=False, allow_null=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(source='tags', many=True, queryset=Tag.objects.all(), write_only=True, required=False)
    requirements = RequirementSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(source='get_average_rating', read_only=True)

    class Meta:
        model = Hobby
        fields = [
            'id','host','title','description','category','category_id','tags','tag_ids','image',
            'max_participants','date','place','province','city','neighbourhood','created_at','requirements','average_rating'
        ]

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        hobby = Hobby.objects.create(**validated_data)
        if tags:
            hobby.tags.set(tags)
        return hobby

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        return instance

class ApplicationSerializer(serializers.ModelSerializer):
    applicant = UserSerializer(read_only=True)
    class Meta:
        model = Application
        fields = ['id','hobby','applicant','status','applied_at']
        read_only_fields = ['status']

class RatingSerializer(serializers.ModelSerializer):
    rater = UserSerializer(read_only=True)
    class Meta:
        model = Rating
        fields = ['id','hobby','rater','score','anonymous','comment']

class ParticipantRatingSerializer(serializers.ModelSerializer):
    host = UserSerializer(read_only=True)
    participant = UserSerializer(read_only=True)
    class Meta:
        model = ParticipantRating
        fields = ['id','hobby','host','participant','score','comment']

    def validate_score(self, value):
        if value not in [1,2,3,4,5]:
            raise serializers.ValidationError('Score must be 1-5')
        return value

class SupplierSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Supplier
        fields = ['id','user','province','city','neighbourhood','active','created_at']

class SupplierItemSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(source='category', queryset=Category.objects.all(), write_only=True, required=False, allow_null=True)
    tag = TagSerializer(read_only=True)
    tag_id = serializers.PrimaryKeyRelatedField(source='tag', queryset=Tag.objects.all(), write_only=True, required=False, allow_null=True)
    class Meta:
        model = SupplierItem
        fields = ['id','supplier','name','category','category_id','tag','tag_id','quantity','is_rental','price','image','created_at']
