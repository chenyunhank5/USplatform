from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.staff_home, name='staff_home'),
    path('staff/user-management/', views.staff_user_management, name='staff_user_management'),
    path('staff/user/add/', views.staff_add_user, name='staff_add_user'),
    path('staff/user/<int:profile_id>/score/', views.staff_score_modify, name='staff_score_modify'),
    path('staff/user/<int:profile_id>/edit/', views.staff_edit_user, name='staff_edit_user'),

    path('staff/vip-levels/', views.staff_vip_level_management, name='staff_vip_level_management'),
    path('staff/vip-level/add/', views.staff_add_vip_level, name='staff_add_vip_level'),
    path('staff/vip-level/<int:vip_id>/edit/', views.staff_edit_vip_level, name='staff_edit_vip_level'),
    path('staff/vip-level/<int:vip_id>/delete/', views.staff_delete_vip_level, name='staff_delete_vip_level'),

    path('staff/product-list/', views.staff_product_list, name='staff_product_list'),
    path('staff/product/add/', views.staff_add_product, name='staff_add_product'),
    path('staff/product/<int:product_id>/edit/', views.staff_edit_product, name='staff_edit_product'),
    path('staff/product/<int:product_id>/delete/',views.staff_delete_product,name='staff_delete_product'),

    path('staff/product-evaluation/', views.staff_product_evaluation, name='staff_product_evaluation'),
    path('staff/product-evaluation/add/', views.staff_add_product_evaluation, name='staff_add_product_evaluation'),
    path('staff/product-evaluation/<int:comment_id>/edit/', views.staff_edit_product_evaluation, name='staff_edit_product_evaluation'),
    path('staff/product-evaluation/<int:comment_id>/delete/', views.staff_delete_product_evaluation, name='staff_delete_product_evaluation'),

    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('register/', views.user_register, name='user_register'),

    path('user/home/', views.user_home, name='user_home'),
    path('user/records/', views.user_records, name='user_records'),
    path('user/order/', views.user_order, name='user_order'),
    path('user/messages/', views.user_messages, name='user_messages'),
    path('user/settings/', views.user_settings, name='user_settings'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
