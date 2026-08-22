from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User, UserPreference


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "name", "role")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("このメールアドレスは既に登録されています。")
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email", "name")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.exclude(pk=self.instance.pk).filter(email__iexact=email).exists():
            raise forms.ValidationError("このメールアドレスは既に登録されています。")
        return email


class UserPreferenceForm(forms.ModelForm):
    class Meta:
        model = UserPreference
        fields = ("desired_location", "notifications_enabled", "theme_color")


class AccountDeletionForm(forms.Form):
    password = forms.CharField(label="現在のパスワード", widget=forms.PasswordInput)
    confirmation = forms.BooleanField(label="アカウント削除に同意します")

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_password(self):
        password = self.cleaned_data["password"]
        if not self.user.check_password(password):
            raise forms.ValidationError("パスワードが正しくありません。")
        return password
