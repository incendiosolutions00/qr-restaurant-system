from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.tenants.models import Restaurant

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    restaurant_name = serializers.CharField(write_only=True)
    restaurant_slug = serializers.SlugField(write_only=True)
    restaurant_description = serializers.CharField(write_only=True, required=False, allow_blank=True)
    restaurant_address = serializers.CharField(write_only=True, required=False, allow_blank=True)
    restaurant_city = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'role',
            'restaurant_name', 'restaurant_slug',
            'restaurant_description', 'restaurant_address', 'restaurant_city',
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'role': {'required': False},
        }

    def validate_restaurant_slug(self, value):
        if Restaurant.objects.filter(slug=value).exists():
            raise serializers.ValidationError('A restaurant with this slug already exists.')
        return value

    def validate(self, data):
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        rest_name = validated_data.pop('restaurant_name')
        rest_slug = validated_data.pop('restaurant_slug')
        rest_desc = validated_data.pop('restaurant_description', '')
        rest_address = validated_data.pop('restaurant_address', '')
        rest_city = validated_data.pop('restaurant_city', '')

        validated_data['role'] = 'restaurant_owner'
        user = User(**validated_data)
        user.set_password(password)
        user.save()

        restaurant = Restaurant.objects.create(
            name=rest_name,
            slug=rest_slug,
            description=rest_desc,
            address=rest_address or 'Not provided',
            city=rest_city or 'Not provided',
            phone=user.phone or '',
            email=user.email or '',
            owner=user,
        )
        user.restaurant = restaurant
        user.save(update_fields=['restaurant'])

        return user


class UserSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True, default=None)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'role', 'restaurant', 'restaurant_name', 'avatar',
            'is_active', 'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']


class StaffSerializer(serializers.ModelSerializer):
    """For restaurant owners to manage their staff."""
    password = serializers.CharField(write_only=True, min_length=8, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'password', 'first_name', 'last_name',
            'phone', 'role', 'is_active', 'avatar',
        ]
        read_only_fields = ['id']

    def validate_role(self, value):
        allowed = ['manager', 'staff', 'kitchen']
        if value not in allowed:
            raise serializers.ValidationError(f'Staff role must be one of: {", ".join(allowed)}')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        restaurant = self.context['request'].user.restaurant
        user = User(**validated_data, restaurant=restaurant)
        if password:
            user.set_password(password)
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate_old_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('Incorrect current password.')
        return value
