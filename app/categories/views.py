from rest_framework.generics import ListAPIView

from .models import Category
from .serializers import CategorySerializer


class CategoryListAPIView(ListAPIView):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()
