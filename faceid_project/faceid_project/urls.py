"""
URL configuration for faceid_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from biometric.views import home, register, login_view, logout_view, upload_face, face_verify, face_login, diary_list, diary_create, diary_edit, diary_delete
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('upload_face/', upload_face, name='upload_face'),
    path('face_verify/', face_verify, name='face_verify'),
    path('face_login/', face_login, name='face_login'),
    path('diary/', diary_list, name='diary_list'),
    path('diary/create/', diary_create, name='diary_create'),
    path('diary/edit/<int:pk>/', diary_edit, name='diary_edit'),
    path('diary/delete/<int:pk>/', diary_delete, name='diary_delete'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)