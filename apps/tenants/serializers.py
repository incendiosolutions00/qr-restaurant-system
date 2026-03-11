from rest_framework import serializers

from apps.tenants.models import Restaurant, Table, TableSession


class RestaurantSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    owner_id = serializers.IntegerField(source='owner.id', read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    owner_first_name = serializers.CharField(source='owner.first_name', read_only=True)
    owner_last_name = serializers.CharField(source='owner.last_name', read_only=True)
    owner_phone = serializers.CharField(source='owner.phone', read_only=True)
    is_open = serializers.BooleanField(read_only=True)
    table_count = serializers.IntegerField(source='tables.count', read_only=True)
    plan_name = serializers.SerializerMethodField()
    plan_id = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = [
            'id', 'owner', 'owner_name', 'owner_id', 'owner_username',
            'owner_email', 'owner_first_name', 'owner_last_name', 'owner_phone',
            'name', 'slug', 'description', 'logo',
            'address', 'city', 'state', 'country', 'phone', 'email', 'website',
            'currency', 'tax_rate', 'service_charge_rate', 'operating_hours',
            'is_active', 'is_approved', 'is_open', 'is_manually_closed',
            'closure_reason', 'table_count',
            'plan_name', 'plan_id', 'subscription_status',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'owner', 'slug', 'is_approved', 'created_at', 'updated_at']

    def get_plan_name(self, obj):
        sub = getattr(obj, 'subscription', None)
        if sub is None:
            try:
                sub = obj.subscription
            except Exception:
                return None
        return sub.plan.name if sub else None

    def get_plan_id(self, obj):
        try:
            return obj.subscription.plan_id
        except Exception:
            return None

    def get_subscription_status(self, obj):
        try:
            return obj.subscription.status
        except Exception:
            return None


class RestaurantPublicSerializer(serializers.ModelSerializer):
    """Minimal info shown to customers when they scan QR."""
    is_open = serializers.BooleanField(read_only=True)
    closure_status = serializers.DictField(read_only=True)

    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'slug', 'description', 'logo',
            'address', 'city', 'phone', 'currency',
            'tax_rate', 'service_charge_rate', 'operating_hours', 'is_open',
            'closure_status',
        ]


class TableSerializer(serializers.ModelSerializer):
    qr_code_url = serializers.SerializerMethodField()

    class Meta:
        model = Table
        fields = [
            'id', 'restaurant', 'number', 'name', 'capacity',
            'status', 'qr_code', 'qr_code_url', 'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'restaurant', 'qr_code', 'created_at', 'updated_at']

    def get_qr_code_url(self, obj):
        if obj.qr_code:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.qr_code.url)
        return None


class TableSessionSerializer(serializers.ModelSerializer):
    table_number = serializers.IntegerField(source='table.number', read_only=True)

    class Meta:
        model = TableSession
        fields = [
            'id', 'table', 'table_number', 'session_id',
            'started_at', 'ended_at', 'is_active', 'guest_count',
        ]
        read_only_fields = ['id', 'session_id', 'started_at', 'ended_at']
