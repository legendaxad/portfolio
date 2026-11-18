import time

from django import forms
from django.core import signing

from blog.models import Contact

TS_SALT = "contact-form-ts"
MIN_SECONDS = 2          # humans don't submit a full form faster than this
MAX_AGE = 60 * 60 * 24   # token valid for a day


def make_form_token():
    return signing.dumps(int(time.time()), salt=TS_SALT)


class ContactForm(forms.ModelForm):
    # Honeypot field for bot mitigation (hidden from humans & assistive tech)
    honeypot = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'hp-field', 'tabindex': '-1', 'autocomplete': 'off', 'aria-hidden': 'true',
        }),
        label=''
    )
    # Signed render timestamp: rejects instant, scripted submissions.
    ts = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Contact
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'field__input', 'placeholder': ' ',
                'required': True, 'autocomplete': 'name', 'maxlength': 150,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'field__input', 'placeholder': ' ',
                'required': True, 'autocomplete': 'email',
            }),
            'subject': forms.TextInput(attrs={
                'class': 'field__input', 'placeholder': ' ', 'maxlength': 200,
            }),
            'message': forms.Textarea(attrs={
                'class': 'field__input field__input--area', 'placeholder': ' ',
                'rows': 5, 'required': True, 'minlength': 10, 'maxlength': 5000,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields['ts'].initial = make_form_token()

    def clean_name(self):
        name = " ".join(self.cleaned_data.get('name', '').split())
        if len(name) < 2:
            raise forms.ValidationError("Please enter your name.")
        return name

    def clean_message(self):
        message = self.cleaned_data.get('message', '').strip()
        if len(message) < 10:
            raise forms.ValidationError("Please write at least a short sentence (10+ characters).")
        if len(message) > 5000:
            raise forms.ValidationError("Message is too long (5000 characters max).")
        if message.lower().count('http') > 3:
            raise forms.ValidationError("Too many links in the message.")
        return message

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('honeypot'):
            raise forms.ValidationError("Spam detected.")
        token = cleaned_data.get('ts')
        if token:
            try:
                rendered = signing.loads(token, salt=TS_SALT, max_age=MAX_AGE)
            except signing.BadSignature:
                raise forms.ValidationError("This form has expired. Please reload the page and try again.")
            if time.time() - rendered < MIN_SECONDS:
                raise forms.ValidationError("Submitted too quickly. Please try again.")
        return cleaned_data
