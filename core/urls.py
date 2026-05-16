from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # STAFF LOGIN
    path('staff/login/', views.staff_login, name='staff_login'),
    path('staff/logout/', views.staff_logout, name='staff_logout'),

    # STAFF HOME
    path('', views.staff_home, name='staff_home'),

    # STAFF USER MANAGEMENT
    path('staff/user-management/', views.staff_user_management, name='staff_user_management'),
    path('staff/user/add/', views.staff_add_user, name='staff_add_user'),
    path('staff/user/<int:profile_id>/edit/', views.staff_edit_user, name='staff_edit_user'),
    path('staff/user/<int:profile_id>/score/', views.staff_score_modify, name='staff_score_modify'),

    # STAFF USER SECURITY
    path('staff/user/<int:profile_id>/login-password/', views.staff_update_login_password, name='staff_update_login_password'),
    path('staff/user/<int:profile_id>/withdrawal-password/', views.staff_update_withdrawal_password, name='staff_update_withdrawal_password'),
    path('staff/user/<int:profile_id>/wallet-address/', views.staff_update_wallet_address, name='staff_update_wallet_address'),

    # VIP LEVEL MANAGEMENT
    path('staff/vip-levels/', views.staff_vip_level_management, name='staff_vip_level_management'),
    path('staff/vip-level/add/', views.staff_add_vip_level, name='staff_add_vip_level'),
    path('staff/vip-level/<int:vip_id>/edit/', views.staff_edit_vip_level, name='staff_edit_vip_level'),
    path('staff/vip-level/<int:vip_id>/delete/', views.staff_delete_vip_level, name='staff_delete_vip_level'),

    # PRODUCT MANAGEMENT
    path('staff/product-list/', views.staff_product_list, name='staff_product_list'),
    path('staff/product/add/', views.staff_add_product, name='staff_add_product'),
    path('staff/product/<int:product_id>/edit/', views.staff_edit_product, name='staff_edit_product'),
    path('staff/product/<int:product_id>/delete/', views.staff_delete_product, name='staff_delete_product'),

    path('user/withdraw/', views.user_withdraw, name='user_withdraw'),

    path('staff/withdrawals/', views.staff_withdrawal_management, name='staff_withdrawal_management'),
    path('staff/withdrawal/<int:withdrawal_id>/approve/', views.staff_approve_withdrawal, name='staff_approve_withdrawal'),
    path('staff/withdrawal/<int:withdrawal_id>/reject/', views.staff_reject_withdrawal, name='staff_reject_withdrawal'),

    # PRODUCT EVALUATION
    path('staff/product-evaluation/', views.staff_product_evaluation, name='staff_product_evaluation'),
    path('staff/product-evaluation/add/', views.staff_add_product_evaluation, name='staff_add_product_evaluation'),
    path('staff/product-evaluation/<int:comment_id>/edit/', views.staff_edit_product_evaluation, name='staff_edit_product_evaluation'),
    path('staff/product-evaluation/<int:comment_id>/delete/', views.staff_delete_product_evaluation, name='staff_delete_product_evaluation'),

    # USER AUTH
    path('login/', views.user_login, name='user_login'),
    path('user/verify-withdrawal-password/', views.verify_withdrawal_password, name='verify_withdrawal_password'),
    path('logout/', views.user_logout, name='user_logout'),
    path('register/', views.user_register, name='user_register'),

    # USER PAGES
    path('user/home/', views.user_home, name='user_home'),
    path('user/withdraw/', views.user_withdraw, name='user_withdraw'),
    path('user/records/', views.user_records, name='user_records'),
    path('user/order/', views.user_order, name='user_order'),
    path('user/messages/', views.user_messages, name='user_messages'),
    path('user/settings/', views.user_settings, name='user_settings'),
    path('user/trading-account/', views.user_trading_account, name='user_trading_account'),
    path('user/personal-information/', views.user_personal_information, name='user_personal_information'),
    path('user/update-email/', views.user_update_email, name='user_update_email'),
    path('user/update-password/', views.user_update_password, name='user_update_password'),
    path('user/update-transaction-password/', views.user_update_transaction_password, name='user_update_transaction_password'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
