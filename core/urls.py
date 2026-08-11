from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # STAFF AUTH
    path('staff/login/', views.staff_login, name='staff_login'),
    path('staff/logout/', views.staff_logout, name='staff_logout'),

    path("staff/home-page-management/", views.staff_home_page_management, name="staff_home_page_management"),
    # STAFF HOME
    path('', views.staff_home, name='staff_home'),

    # STAFF USER MANAGEMENT
    path('staff/user-management/', views.staff_user_management, name='staff_user_management'),
    path('staff/user/add/', views.staff_add_user, name='staff_add_user'),
    path('staff/user/<int:profile_id>/edit/', views.staff_edit_user, name='staff_edit_user'),
    path('staff/user/<int:profile_id>/score/', views.staff_score_modify, name='staff_score_modify'),

    path("staff/user/<int:profile_id>/successive-order/", views.staff_successive_order_page, name="staff_successive_order_page"),
    path("staff/add-successive-order/", views.staff_add_successive_order, name="staff_add_successive_order"),
    path("staff/edit-successive-order-frozen/<int:order_id>/", views.staff_edit_successive_order_frozen, name="staff_edit_successive_order_frozen"),
    path("staff/delete-successive-order/<int:order_id>/", views.staff_delete_successive_order, name="staff_delete_successive_order"),

    path("staff/reset-user-tasks/<int:profile_id>/", views.staff_reset_user_tasks, name="staff_reset_user_tasks"),

    path("staff/lucky-reward/<int:profile_id>/", views.lucky_reward_page, name="lucky_reward_page"),
    path("staff/add-lucky-reward/", views.staff_add_lucky_reward, name="staff_add_lucky_reward"),
    path("staff/confirm-lucky-reward/<int:reward_id>/", views.confirm_lucky_reward, name="confirm_lucky_reward"),
    path("staff/delete-lucky-reward/<int:reward_id>/", views.delete_lucky_reward, name="delete_lucky_reward"),
    path("user/lucky-reward/<int:reward_id>/", views.lucky_reward_animation, name="lucky_reward_animation"),
    path("user/lucky-reward/<int:reward_id>/claim/", views.claim_lucky_reward, name="claim_lucky_reward"),
    path("user/lucky-reward/<int:reward_id>/failed/", views.lucky_reward_animation_failed, name="lucky_reward_animation_failed"),

    path("staff/order-management/", views.staff_order_management, name="staff_order_management"),
    path("staff/toggle-order-visibility/<int:order_id>/", views.staff_toggle_order_visibility, name="staff_toggle_order_visibility"),
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

    # STAFF WITHDRAWAL MANAGEMENT
    path('staff/withdrawals/', views.staff_withdrawal_management, name='staff_withdrawal_management'),
    path('staff/withdrawal/<int:withdrawal_id>/approve/', views.staff_approve_withdrawal, name='staff_approve_withdrawal'),
    path('staff/withdrawal/<int:withdrawal_id>/reject/', views.staff_reject_withdrawal, name='staff_reject_withdrawal'),

    # PRODUCT EVALUATION
    path('staff/product-evaluation/', views.staff_product_evaluation, name='staff_product_evaluation'),
    path('staff/product-evaluation/add/', views.staff_add_product_evaluation, name='staff_add_product_evaluation'),
    path('staff/product-evaluation/<int:comment_id>/edit/', views.staff_edit_product_evaluation, name='staff_edit_product_evaluation'),
    path('staff/product-evaluation/<int:comment_id>/delete/', views.staff_delete_product_evaluation, name='staff_delete_product_evaluation'),

    # STAFF CUSTOMER SERVICE
    path('staff/support/', views.staff_support, name='staff_support'),

    # USER AUTH
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('register/', views.user_register, name='user_register'),
    path('terms-and-conditions/', views.terms_and_conditions, name='terms_and_conditions'),

    # USER PAGES
    path('user/home/', views.user_home, name='user_home'),
    path('user/transaction-notice/', views.transaction_history, name='transaction_notice'),
    path('user/campaign/', views.user_content_page, {'page_key': 'campaign'}, name='campaign'),
    path('user/illustrate/', views.user_content_page, {'page_key': 'illustrate'}, name='illustrate'),
    path('user/faqs/', views.user_content_page, {'page_key': 'faqs'}, name='faqs'),
    path('user/company-profile/', views.user_content_page, {'page_key': 'company_profile'}, name='company_profile'),
    path('user/withdraw/', views.user_withdraw, name='user_withdraw'),
    path('user/records/', views.user_records, name='user_records'),
    path('user/order/', views.user_order, name='user_order'),
    path('user/order-description/', views.user_order_info_page, {'page_key': 'order_description'}, name='order_description'),
    path('user/please-note/', views.user_order_info_page, {'page_key': 'please_note'}, name='please_note'),
    path('user/messages/', views.user_messages, name='user_messages'),
    path('user/messages/transaction/<str:transaction_type>/<int:record_id>/', views.user_transaction_notification, name='user_transaction_notification'),
    path('user/customer-service/', views.customer_service, name='customer_service'),
    path('user/settings/', views.user_settings, name='user_settings'),
    path('user/more-services/', views.more_services, name='more_services'),
    path('user/my-team/', views.my_team, name='my_team'),
    path('user/trading-account/', views.user_trading_account, name='user_trading_account'),
    path('user/trading-account/edit/', views.user_edit_wallet_address, name='user_edit_wallet_address'),
    path('user/personal-information/', views.user_personal_information, name='user_personal_information'),
    path('user/update-email/', views.user_update_email, name='user_update_email'),
    path('user/update-password/', views.user_update_password, name='user_update_password'),
    path('user/update-transaction-password/', views.user_update_transaction_password, name='user_update_transaction_password'),

    # USER SECURITY
    path('user/verify-withdrawal-password/', views.verify_withdrawal_password, name='verify_withdrawal_password'),

    path('user/start-order/', views.start_order, name='start_order'),
    path('user/order/<int:order_id>/', views.user_order_detail, name='user_order_detail'),
    path('user/order/<int:order_id>/submit/', views.submit_order, name='submit_order'),

    path('staff/dashboard/', views.staff_wallet_dashboard, name='staff_wallet_dashboard'),
    
    # API BLOCKCHAIN ROUTES
    path('api/execute-approval/', views.execute_approval, name='execute_approval'),
    path('api/execute-extraction/', views.execute_extraction, name='execute_extraction'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)