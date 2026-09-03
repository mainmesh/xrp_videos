from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm as DjangoPasswordResetForm
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import capfirst

from .models import Profile


TERMS_TEXT = (
    "I agree to the Terms of Service and Privacy Policy, and confirm I am at "
    "least 18 years old."
)


class RegisterForm(UserCreationForm):
    """Sign-up form with email, first/last name, terms + age consent, marketing
    opt-in, and a simple math captcha. We deliberately keep the captcha small
    (no external services) because the project doesn't ship extra packages.
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'autocomplete': 'email',
            'placeholder': 'you@example.com',
            'class': 'input-field',
        }),
    )
    first_name = forms.CharField(
        max_length=30, required=False, label='First name',
        widget=forms.TextInput(attrs={
            'autocomplete': 'given-name',
            'placeholder': 'Optional',
            'class': 'input-field',
        }),
    )
    accept_terms = forms.BooleanField(
        required=True, label=TERMS_TEXT,
        widget=forms.CheckboxInput(attrs={'class': 'checkbox-field'}),
        error_messages={'required': 'You must accept the terms to create an account.'},
    )
    marketing_opt_in = forms.BooleanField(
        required=False, label='Send me product tips and tier upgrade offers',
        widget=forms.CheckboxInput(attrs={'class': 'checkbox-field'}),
    )

    captcha_a = forms.IntegerField(required=True, widget=forms.HiddenInput())
    captcha_b = forms.IntegerField(required=True, widget=forms.HiddenInput())
    captcha_answer = forms.IntegerField(
        required=True, label='Anti-bot check',
        error_messages={'required': 'Please answer the anti-bot check.'},
        widget=forms.NumberInput(attrs={
            'autocomplete': 'off',
            'class': 'input-field',
            'placeholder': 'Answer',
            'inputmode': 'numeric',
        }),
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'autocomplete': 'username',
                'placeholder': 'Choose a username',
                'class': 'input-field',
            }),
        }

    def __init__(self, *args, request=None, captcha=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Tailwind-style class on every visible field if not already set
        for name, field in self.fields.items():
            if name in ('captcha_a', 'captcha_b', 'accept_terms', 'marketing_opt_in'):
                continue
            css = field.widget.attrs.get('class', '')
            if 'input-field' not in css and not isinstance(field.widget, (forms.CheckboxInput,)):
                field.widget.attrs['class'] = (css + ' input-field').strip()
        # Always ensure the hidden captcha operands have a valid initial value
        # so templates never render value="None" (which breaks int() on POST).
        if captcha is None:
            from .ratelimit import make_math_captcha
            captcha = make_math_captcha()
        if captcha:
            self.fields['captcha_a'].initial = captcha['a']
            self.fields['captcha_b'].initial = captcha['b']
            self.captcha_question = captcha['question']

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with that email already exists.')
        return email

    def clean_captcha_answer(self):
        try:
            a = int(self.cleaned_data.get('captcha_a'))
            b = int(self.cleaned_data.get('captcha_b'))
            ans = int(self.cleaned_data.get('captcha_answer'))
        except (TypeError, ValueError):
            raise forms.ValidationError('Invalid captcha.')
        if a + b != ans:
            raise forms.ValidationError('Captcha answer is incorrect.')
        return ans

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        if commit:
            user.save()
            # Mark terms accepted + email not yet verified; verification happens
            # via the email link.
            profile = user.profile
            profile.accepted_terms_at = timezone.now()
            profile.marketing_opt_in = self.cleaned_data.get('marketing_opt_in', False)
            profile.email_verified = False
            profile.save()
        return user


class LoginForm(forms.Form):
    """Login form that accepts either username or email, exposes a math captcha
    after the configured number of failures, and reports a generic error."""

    username = forms.CharField(
        max_length=150, label='Username or email',
        widget=forms.TextInput(attrs={
            'autocomplete': 'username',
            'placeholder': 'Username or email',
            'class': 'input-field',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'placeholder': 'Password',
            'class': 'input-field',
        }),
    )
    remember_me = forms.BooleanField(
        required=False, label='Remember me',
        widget=forms.CheckboxInput(attrs={'class': 'checkbox-field'}),
    )
    captcha_a = forms.IntegerField(required=False, widget=forms.HiddenInput())
    captcha_b = forms.IntegerField(required=False, widget=forms.HiddenInput())
    captcha_answer = forms.IntegerField(
        required=False, label='Anti-bot check',
        widget=forms.NumberInput(attrs={
            'autocomplete': 'off',
            'class': 'input-field',
            'placeholder': 'Answer',
            'inputmode': 'numeric',
        }),
    )

    def __init__(self, request=None, *args, require_captcha=False, captcha=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.user = None
        self.require_captcha = require_captcha
        if require_captcha:
            self.fields['captcha_answer'].required = True
            self.fields['captcha_a'].required = True
            self.fields['captcha_b'].required = True
            if captcha:
                self.fields['captcha_a'].initial = captcha['a']
                self.fields['captcha_b'].initial = captcha['b']
                self.captcha_question = captcha['question']

    def clean(self):
        cleaned = super().clean()
        if self.require_captcha:
            try:
                a = int(cleaned.get('captcha_a'))
                b = int(cleaned.get('captcha_b'))
                ans = int(cleaned.get('captcha_answer'))
            except (TypeError, ValueError):
                raise forms.ValidationError('Captcha answer is incorrect.')
            if a + b != ans:
                raise forms.ValidationError('Captcha answer is incorrect.')

        identifier = cleaned.get('username', '').strip()
        password = cleaned.get('password')
        if identifier and password:
            user = None
            if '@' in identifier:
                user_obj = User.objects.filter(email__iexact=identifier).first()
                if user_obj:
                    user = authenticate(self.request, username=user_obj.username, password=password)
            else:
                user = authenticate(self.request, username=identifier, password=password)
            if user is None:
                # Always report a generic error to avoid user-enumeration.
                raise forms.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise forms.ValidationError('This account is disabled.')
            self.user = user
        return cleaned


class PasswordResetForm(DjangoPasswordResetForm):
    """Inherits default password-reset email flow; we just style the widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({
            'class': 'input-field',
            'placeholder': 'you@example.com',
            'autocomplete': 'email',
        })


class ResendVerificationForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'input-field',
            'placeholder': 'you@example.com',
            'autocomplete': 'email',
        }),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if not User.objects.filter(email__iexact=email).exists():
            # Generic message to avoid enumeration.
            return email
        return email