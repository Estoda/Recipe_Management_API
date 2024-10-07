from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register(r'recipes', views.RecipeViewSet, basename='recipe')
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.Register.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('user/', views.UserView.as_view(), name='user'),
    path('user/recipes/', views.RecipeView.as_view(), name='user-recipes'),
    path('user/recipes/<int:recipe_id>/', views.RecipeView.as_view(), name='user-recipes-detail'),
    path('api/', include(router.urls), name='recipe'),
]