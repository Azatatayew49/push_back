from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('register/', views.register_device_token, name='register_device_token'),
    path('unregister/', views.unregister_device_token, name='unregister_device_token'),
    path('test/', views.send_test_notification, name='send_test_notification'),
    path('mock-test/', views.mock_send_notification, name='mock_send_notification'),
    path('test-connection/', views.test_connection, name='test_connection'),
]
