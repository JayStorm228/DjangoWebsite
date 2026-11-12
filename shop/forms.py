from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Review


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label="Email", required=True)
    first_name = forms.CharField(label="Имя", max_length=150, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "first_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Поле появилось в Django 5.1 и не нужно для обычной регистрации.
        self.fields.pop("usable_password", None)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "text")
        widgets = {
            "rating": forms.Select(
                choices=[(value, f"{value} из 5") for value in range(5, 0, -1)],
                attrs={"class": "form-select"},
            ),
            "text": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Поделитесь впечатлением о курсе",
                }
            ),
        }


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
