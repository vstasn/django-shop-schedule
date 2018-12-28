from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from .serializers import UserSerializer, ShopSerializer, ShopCloseSerializer, ShopUpdateSerialized
from .models import Shop


@api_view(["POST"])
@permission_classes((permissions.AllowAny,))
def create_user(request):
    serialized = UserSerializer(data=request.data)
    if serialized.is_valid():
        serialized.save()
        return Response(serialized.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serialized._errors, status=status.HTTP_400_BAD_REQUEST)


class IsOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj=None):
        '''allow to get object if AnyAllow permission is set'''
        return obj.owner == request.user


class ShopDetail(viewsets.ModelViewSet):
    """
    Retrieve, update or delete a shop instance.
    """
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    permission_classes = [IsOwner, permissions.IsAuthenticated]

    def create(self, request):
        serializer = ShopSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=True, )
    def update_schedule(self, request, pk=None):
        shop = self.get_object()
        serializer = ShopUpdateSerialized(data=request.data, context={'request': request})

        if serializer.is_valid():
            updated = serializer.update_schedule(shop, serializer.validated_data)
            return Response({'updated': updated})
        else:
            return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=True, )
    def close(self, request, pk):
        shop = self.get_object()
        serializer = ShopCloseSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(shop=shop)
            return Response(serializer.data)
        else:
            return Response(serializer._errors, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=True, permission_classes=[permissions.AllowAny])
    def is_working(self, request, pk):
        shop = self.get_object()
        serializer = ShopSerializer(shop)

        is_working = serializer.is_working(shop)

        return Response({'is_working': is_working})

    @action(methods=['post'], detail=True, permission_classes=[permissions.AllowAny])
    def schedule(self, request, pk):
        shop = self.get_object()
        serializer = ShopSerializer(shop, data=request.data, context={'request': request})

        schedule = serializer.schedule(shop)

        return Response({'working_hours': schedule})
