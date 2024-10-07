from django.db.models import Q
from rest_framework import viewsets
from .serializers import RecipeSerializer, UserSerializer
from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import Recipe, User
from rest_framework.permissions import  IsAuthenticated
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
import jwt, datetime
from django.conf import settings
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.pagination import PageNumberPagination

# pagination details
class RecipePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

# hom page html template
def home(request):
    return render(request, 'recipe/home.html')

# view to display all users (only the admin or superusers can use it)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

# view to display all recipes (only the admin or superusers can use it)
class RecipeViewSet(viewsets.ModelViewSet):
    serializer_class = RecipeSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = RecipePagination

    # and the search by title, category, ingredients, cooking_time, servings and preparation_time
    def get_queryset(self):
        queryset = Recipe.objects.all()
        
        title_query = self.request.query_params.get('title', None)
        if title_query:
            queryset = queryset.filter(title__icontains=title_query)

        category_query = self.request.query_params.get('category', None)
        if category_query:
            queryset = queryset.filter(category__iexact=category_query)

        ingredients_query = self.request.query_params.get('ingredients', None)
        if ingredients_query:
            queryset = queryset.filter(ingredients__icontains=ingredients_query)

        cooking_time_query = self.request.query_params.get('cooking_time', None)
        if cooking_time_query:
            queryset = queryset.filter(cooking_time=cooking_time_query)

        servings_query = self.request.query_params.get('servings', None)
        if servings_query:
            queryset = queryset.filter(servings=servings_query)

        preparation_time_query = self.request.query_params.get('preparation_time', None)
        if preparation_time_query:
            queryset = queryset.filter(preparation_time=preparation_time_query)
        
        # Sorting:
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            allowed_sort_field = ['preparation_time', 'cooking_time', 'servings', 'created_at']
            if ordering.strip('-') in allowed_sort_field:
                queryset = queryset.order_by(ordering)
            else:
                return Response({'detail': 'Invalid ordering field'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Pagination
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, self.request)
        serializer = RecipeSerializer(paginated_queryset, many=True)

        return queryset

# view to show the current user details. using the token in the cookies
class UserView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Unauthenticated!, Login please')
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated!')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token!')
        
        user = User.objects.filter(id=payload['id']).first() # first() just to be safe (id is unique attribute)
        serializer = UserSerializer(user)
        if not user:
            raise AuthenticationFailed('User not found!')
        
        return Response(serializer.data)
    
#view to display only the current user's recipes using the token in the cookies
class RecipeView(APIView):
    serializer_class = RecipeSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = PageNumberPagination

    def get(self, request, recipe_id=None):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Unauthenticated!, Login please')
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated!')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token!')
        
        user = User.objects.filter(id=payload['id']).first()
        queryset = Recipe.objects.all()
        if not user:
            raise AuthenticationFailed('User not found!')
        
        queryset = queryset.filter(user=user)

        if recipe_id:
            recipe = Recipe.objects.filter(id=recipe_id, user=user).first()
            if not recipe:
                raise Response({'detail': 'Recipe not found!'}, status=status.HTTP_404_NOT_FOUND)
            serializer = RecipeSerializer(recipe)
            return Response(serializer.data)

        # now the search by title, category, ingredients, cooking_time, servings and preparation_time
        title_query = self.request.query_params.get('title', None)
        if title_query:
            queryset = queryset.filter(title__icontains=title_query)

        category_query = self.request.query_params.get('category', None)
        if category_query:
            queryset = queryset.filter(category__iexact=category_query)

        ingredients_query = self.request.query_params.get('ingredients', None)
        if ingredients_query:
            queryset = queryset.filter(ingredients__icontains=ingredients_query)

        cooking_time_query = self.request.query_params.get('cooking_time', None)
        if cooking_time_query:
            queryset = queryset.filter(cooking_time=cooking_time_query)

        servings_query = self.request.query_params.get('servings', None)
        if servings_query:
            queryset = queryset.filter(servings=servings_query)

        preparation_time_query = self.request.query_params.get('preparation_time', None)
        if preparation_time_query:
            queryset = queryset.filter(preparation_time=preparation_time_query)

        # Sorting:
        ordering = request.query_params.get('ordering', None)
        if ordering:
            allowed_sort_field = ['preparation_time', 'cooking_time', 'servings', 'created_at']
            if ordering.strip('-') in allowed_sort_field:
                queryset = queryset.order_by(ordering)
            else:
                return Response({'detail': 'Invalid ordering field'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Pagination
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = RecipeSerializer(paginated_queryset, many=True)
        
        return paginator.get_paginated_response(serializer.data)
    
    def post(self, request):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Unauthenticated!, Login please')
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated!')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token!')
        
        user = User.objects.filter(id=payload['id']).first()

        if not user:
            raise AuthenticationFailed('User not found!')

        data = request.data.copy()
        if not data['user'] == payload['id']:
            raise AuthenticationFailed('The user must be you!')

        serializer = RecipeSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, recipe_id=None):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Unauthenticated! Please login.')
        try:
            payload = jwt.decode(token,  settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated! Token expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token!')
        
        user = User.objects.filter(id=payload['id']).first()
        if not user:
            raise AuthenticationFailed('User not found!')
        
        recipe = Recipe.objects.filter(id=recipe_id, user=user).first()
        if not recipe:
            return Response({'detail': 'Recipe not found or you do not have permission to update it.'}, status=status.HTTP_404_NOT_FOUND)
        
        data = request.data.copy()
        if not data['user'] == payload['id']:
            raise AuthenticationFailed('The user must be you!')

        serializer = RecipeSerializer(recipe, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, recipe_id=None):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('Unauthenticated! Please login.')
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Unauthenticated! Token expired.')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token!')
        
        user = User.objects.filter(id=payload['id']).first()
        if not user:
            raise AuthenticationFailed('User not found!')
        
        recipe = Recipe.objects.filter(id=recipe_id, user=user).first()
        if not recipe:
            return Response({'detail': 'Recipe not found or you don\'t have permission to delete it!'}, status=status.HTTP_404_NOT_FOUND)
        
        recipe.delete()
        return Response({'detail': 'Recipe deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
# the register view (creating new user)
class Register(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

# the login view in an existing user and saving the token in the cookies using jwt
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        email = request.data['email']
        password = request.data['password']
        user = User.objects.filter(email=email).first() # because the email is unique

        if user is None:
            raise AuthenticationFailed('User not found!')
        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect password!')
        
        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        response = Response()
        response.set_cookie(key='jwt', value=token, httponly=True)
        response.data = {
            'jwt': token,
        }

        return response

# logout view to remove the token from cookies
class LogoutView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {
            'message': 'Logout Done'
        }
        return response

