from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.accounts.permissions import IsManagerOrAbove, IsRestaurantOwner, IsSuperAdmin
from apps.tenants.models import Restaurant, Table, TableSession
from apps.tenants.serializers import (
    RestaurantPublicSerializer, RestaurantSerializer,
    TableSerializer, TableSessionSerializer,
)

User = get_user_model()


# ─── RESTAURANT MANAGEMENT (Owner) ──────────────────────────────────────────

class RestaurantProfileView(generics.RetrieveUpdateAPIView):
    """Restaurant owner views/updates their restaurant profile."""
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.IsAuthenticated, IsRestaurantOwner]

    def get_object(self):
        return Restaurant.objects.get(owner=self.request.user)


# ─── TABLE MANAGEMENT ───────────────────────────────────────────────────────

class TableListCreateView(generics.ListCreateAPIView):
    """List and create tables for the authenticated user's restaurant."""
    serializer_class = TableSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        return Table.objects.filter(restaurant=self.request.user.restaurant)

    def perform_create(self, serializer):
        from apps.core.utils import check_plan_limit
        check_plan_limit(self.request.user.restaurant, 'tables')
        table = serializer.save(restaurant=self.request.user.restaurant)
        table.generate_qr_code()
        table.save()


class TableDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a table."""
    serializer_class = TableSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        return Table.objects.filter(restaurant=self.request.user.restaurant)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsManagerOrAbove])
def regenerate_qr(request, pk):
    """Regenerate QR code for a specific table."""
    try:
        table = Table.objects.get(pk=pk, restaurant=request.user.restaurant)
    except Table.DoesNotExist:
        return Response({'detail': 'Table not found.'}, status=status.HTTP_404_NOT_FOUND)
    table.generate_qr_code()
    table.save()
    return Response(TableSerializer(table, context={'request': request}).data)


# ─── TABLE SESSIONS ─────────────────────────────────────────────────────────

class TableSessionListView(generics.ListAPIView):
    """List active sessions for the restaurant."""
    serializer_class = TableSessionSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        return TableSession.objects.filter(
            table__restaurant=self.request.user.restaurant,
            is_active=True,
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsManagerOrAbove])
def close_session(request, pk):
    """Manually close a table session (bill paid, table cleared)."""
    try:
        session = TableSession.objects.get(
            pk=pk, table__restaurant=request.user.restaurant, is_active=True
        )
    except TableSession.DoesNotExist:
        return Response({'detail': 'Session not found.'}, status=status.HTTP_404_NOT_FOUND)
    session.close_session()
    return Response({'detail': 'Session closed successfully.'})


# ─── SUPER ADMIN — RESTAURANT MANAGEMENT ────────────────────────────────────

class SuperAdminRestaurantListView(generics.ListCreateAPIView):
    """Super admin — list all restaurants or create new ones."""
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    queryset = Restaurant.objects.all()
    filterset_fields = ['is_active', 'is_approved', 'city']
    search_fields = ['name', 'slug', 'city', 'email']


class SuperAdminRestaurantDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Super admin — view, update or delete any restaurant."""
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    queryset = Restaurant.objects.all()


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsSuperAdmin])
def approve_restaurant(request, pk):
    """Super admin approves a restaurant to go live."""
    try:
        restaurant = Restaurant.objects.get(pk=pk)
    except Restaurant.DoesNotExist:
        return Response({'detail': 'Restaurant not found.'}, status=status.HTTP_404_NOT_FOUND)
    restaurant.is_approved = True
    restaurant.is_active = True
    restaurant.save(update_fields=['is_approved', 'is_active', 'updated_at'])
    return Response({'detail': f'{restaurant.name} has been approved.'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsSuperAdmin])
@transaction.atomic
def create_restaurant_with_owner(request):
    """Super admin creates a restaurant + its owner account + subscription in one step."""
    from apps.subscriptions.models import Plan, Subscription

    data = request.data

    # Validate required fields
    required = ['owner_username', 'owner_password', 'name', 'slug', 'address', 'city', 'phone', 'email']
    missing = [f for f in required if not data.get(f)]
    if missing:
        return Response({'detail': f'Missing fields: {", ".join(missing)}'}, status=status.HTTP_400_BAD_REQUEST)

    # Check unique username and slug
    if User.objects.filter(username=data['owner_username']).exists():
        return Response({'detail': 'Username already taken.'}, status=status.HTTP_400_BAD_REQUEST)
    if Restaurant.objects.filter(slug=data['slug']).exists():
        return Response({'detail': 'Restaurant slug already taken.'}, status=status.HTTP_400_BAD_REQUEST)

    # Validate plan if provided
    plan = None
    if data.get('plan_id'):
        try:
            plan = Plan.objects.get(pk=data['plan_id'], is_active=True)
        except Plan.DoesNotExist:
            return Response({'detail': 'Selected plan not found.'}, status=status.HTTP_400_BAD_REQUEST)

    # Create owner user
    owner = User(
        username=data['owner_username'],
        email=data.get('owner_email', data['email']),
        first_name=data.get('owner_first_name', ''),
        last_name=data.get('owner_last_name', ''),
        phone=data.get('owner_phone', data['phone']),
        role='restaurant_owner',
    )
    owner.set_password(data['owner_password'])
    owner.save()

    # Create restaurant
    restaurant = Restaurant.objects.create(
        owner=owner,
        name=data['name'],
        slug=data['slug'],
        description=data.get('description', ''),
        address=data['address'],
        city=data['city'],
        phone=data['phone'],
        email=data['email'],
        is_approved=True,
        is_active=True,
    )

    # Link owner to restaurant
    owner.restaurant = restaurant
    owner.save(update_fields=['restaurant'])

    # Create subscription if plan selected
    if plan:
        from django.utils import timezone
        from dateutil.relativedelta import relativedelta
        today = timezone.now().date()
        if plan.billing_cycle == 'yearly':
            end_date = today + relativedelta(years=1)
        else:
            end_date = today + relativedelta(months=1)
        Subscription.objects.create(
            restaurant=restaurant,
            plan=plan,
            status='active',
            start_date=today,
            end_date=end_date,
        )

    return Response(RestaurantSerializer(restaurant).data, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated, IsSuperAdmin])
def update_restaurant_owner(request, pk):
    """Super admin updates the owner account of a restaurant."""
    try:
        restaurant = Restaurant.objects.get(pk=pk)
    except Restaurant.DoesNotExist:
        return Response({'detail': 'Restaurant not found.'}, status=status.HTTP_404_NOT_FOUND)

    owner = restaurant.owner
    if not owner:
        return Response({'detail': 'This restaurant has no owner.'}, status=status.HTTP_400_BAD_REQUEST)

    data = request.data

    # Update username (check uniqueness)
    if 'username' in data and data['username'] != owner.username:
        if User.objects.filter(username=data['username']).exclude(pk=owner.pk).exists():
            return Response({'detail': 'Username already taken.'}, status=status.HTTP_400_BAD_REQUEST)
        owner.username = data['username']

    # Update email (check uniqueness)
    if 'email' in data and data['email'] != owner.email:
        if data['email'] and User.objects.filter(email=data['email']).exclude(pk=owner.pk).exists():
            return Response({'detail': 'Email already in use.'}, status=status.HTTP_400_BAD_REQUEST)
        owner.email = data['email']

    # Update other fields
    if 'first_name' in data:
        owner.first_name = data['first_name']
    if 'last_name' in data:
        owner.last_name = data['last_name']
    if 'phone' in data:
        owner.phone = data['phone']

    # Update password (optional — only if provided and non-empty)
    if data.get('password'):
        if len(data['password']) < 8:
            return Response({'detail': 'Password must be at least 8 characters.'}, status=status.HTTP_400_BAD_REQUEST)
        owner.set_password(data['password'])

    owner.save()
    return Response({
        'detail': 'Owner account updated.',
        'owner': {
            'id': owner.id,
            'username': owner.username,
            'email': owner.email,
            'first_name': owner.first_name,
            'last_name': owner.last_name,
            'phone': owner.phone,
        }
    })


# ─── PUBLIC / CUSTOMER ───────────────────────────────────────────────────────

class CustomerRestaurantView(generics.RetrieveAPIView):
    """Public — customer views restaurant info after scanning QR."""
    serializer_class = RestaurantPublicSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    queryset = Restaurant.objects.filter(is_active=True, is_approved=True)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def customer_table_info(request, slug, table_id):
    """Public — customer scans QR, gets table info + starts session."""
    try:
        restaurant = Restaurant.objects.get(slug=slug, is_active=True, is_approved=True)
        table = Table.objects.get(pk=table_id, restaurant=restaurant, is_active=True)
    except (Restaurant.DoesNotExist, Table.DoesNotExist):
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Get or create active session for this table
    session, created = TableSession.objects.get_or_create(
        table=table, is_active=True,
        defaults={'guest_count': 1}
    )

    if created:
        table.status = Table.Status.OCCUPIED
        table.save(update_fields=['status', 'updated_at'])

    return Response({
        'restaurant': RestaurantPublicSerializer(restaurant).data,
        'table': TableSerializer(table).data,
        'session': TableSessionSerializer(session).data,
    })
