from django.urls import path

from . import views

app_name = "users"

urlpatterns = [
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    path("register/", views.RegisterView.as_view(), name="register"),
    path("email-confirm/<str:token>/", views.email_verification, name="email_confirm"),
    path("password-reset/", views.UserPasswordResetView.as_view(), name="password_reset"),
    path("password-reset/done/", views.UserPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", views.UserPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", views.UserPasswordResetCompleteView.as_view(), name="password_reset_complete"),
    path("list/", views.UserListView.as_view(), name="user_list"),
    path("<int:pk>/toggle-active/", views.ToggleUserActiveView.as_view(), name="toggle_active"),
]
