from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.permissions import IsManagerOrAbove, IsSuperAdmin
from apps.accounts.serializers import (
    ChangePasswordSerializer, StaffSerializer,
    UserRegistrationSerializer, UserSerializer,
)

User = get_user_model()


# ─── AUTH ────────────────────────────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    """Register a new user (restaurant owner signup)."""
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class ProfileView(generics.RetrieveUpdateAPIView):
    """Get or update current user's profile."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    """Change current user's password."""
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'Password changed successfully.'})


# ─── STAFF MANAGEMENT (Restaurant Owner / Manager) ──────────────────────────

class StaffListCreateView(generics.ListCreateAPIView):
    """List and create staff for the authenticated user's restaurant."""
    serializer_class = StaffSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        return User.objects.filter(
            restaurant=self.request.user.restaurant,
            role__in=['manager', 'staff', 'kitchen'],
        ).order_by('first_name')

    def perform_create(self, serializer):
        from apps.core.utils import check_plan_limit
        check_plan_limit(self.request.user.restaurant, 'staff')
        serializer.save()


class StaffDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a staff member."""
    serializer_class = StaffSerializer
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAbove]

    def get_queryset(self):
        return User.objects.filter(
            restaurant=self.request.user.restaurant,
            role__in=['manager', 'staff', 'kitchen'],
        )

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])


# ─── SUPER ADMIN — USER MANAGEMENT ──────────────────────────────────────────

class SuperAdminUserListView(generics.ListAPIView):
    """Super admin — list all users in the system."""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsSuperAdmin]
    queryset = User.objects.all().order_by('-date_joined')
    filterset_fields = ['role', 'is_active', 'restaurant']
    search_fields = ['username', 'email', 'first_name', 'last_name']
