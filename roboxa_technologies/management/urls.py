from django.urls import path
from .views import LoginView, SendOTPView, ForgotPasswordView,CustomTokenObtainPairView,VerifyOTPView,change_password,login_refresh_token

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('send-otp/', SendOTPView.as_view(), name='send_otp'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('jwt-token/', CustomTokenObtainPairView.as_view(), name='jwt_token'),
    path('change_password/', change_password, name= "change_password"),
    path('refersh_token/',login_refresh_token),
    path('verify_otp/', VerifyOTPView.as_view())
]
