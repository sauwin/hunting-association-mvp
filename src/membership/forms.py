from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import FeeQuote, MemberProfile, PaymentRecord
from .services import DEFAULT_CONSENT_TEXT

User = get_user_model()


class FeeCalculatorPreviewForm(forms.Form):
    member_type = forms.ChoiceField(
        choices=MemberProfile.MemberType.choices,
        initial=MemberProfile.MemberType.HUNTER,
        label="Membership category",
    )
    include_insurance = forms.BooleanField(
        required=False,
        initial=False,
        label="Include hunting liability insurance add-on (sample rate)",
    )
    apply_reduced_rate = forms.BooleanField(
        required=False,
        initial=False,
        label="Apply student / senior reduced-fee discount (sample rate)",
    )


class MembershipApplicationForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=150,
        required=True,
        label="First name",
    )
    last_name = forms.CharField(
        max_length=150,
        required=True,
        label="Last name",
    )
    include_insurance = forms.BooleanField(
        required=False,
        initial=False,
        label="Include optional insurance add-on in my fee quote",
    )
    apply_reduced_rate = forms.BooleanField(
        required=False,
        initial=False,
        label="Request reduced-rate discount (student / senior placeholder)",
    )
    consent_accepted = forms.BooleanField(
        required=True,
        label="I explicitly consent to the processing of my application data",
        help_text=DEFAULT_CONSENT_TEXT,
    )

    class Meta:
        model = MemberProfile
        fields = [
            "member_type",
            "phone",
            "street_address",
            "city",
            "postal_code",
            "hunting_licence_number",
            "licence_valid_until",
            "insurance_valid_until",
        ]
        widgets = {
            "licence_valid_until": forms.DateInput(attrs={"type": "date"}),
            "insurance_valid_until": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None and not self.is_bound:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name

    def clean(self):
        cleaned_data = super().clean()
        valid_from_licence = cleaned_data.get("licence_valid_until")
        licence_number = (cleaned_data.get("hunting_licence_number") or "").strip()

        if valid_from_licence and not licence_number:
            self.add_error(
                "hunting_licence_number",
                "Please provide a hunting licence number when specifying a licence expiry date.",
            )
        return cleaned_data


class MemberStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=MemberProfile.Status.choices,
        label="Membership status",
    )
    valid_from = forms.DateField(
        required=False,
        label="Valid from",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    valid_until = forms.DateField(
        required=False,
        label="Valid until",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    note = forms.CharField(
        max_length=255,
        required=False,
        label="Audit note",
        help_text="Recorded in the member's lifecycle status history.",
    )

    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get("valid_from")
        valid_until = cleaned_data.get("valid_until")

        if valid_from and valid_until and valid_until < valid_from:
            self.add_error(
                "valid_until",
                "Valid-until date cannot be earlier than the valid-from date.",
            )
        return cleaned_data


class ManualPaymentForm(forms.ModelForm):
    class Meta:
        model = PaymentRecord
        fields = [
            "quote",
            "status",
            "amount",
            "currency",
            "reference",
            "payment_date",
            "notes",
        ]
        widgets = {
            "payment_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, member: MemberProfile | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.member = member
        if member is not None:
            quotes_qs = member.fee_quotes.all()
            self.fields["quote"].queryset = quotes_qs
            if not self.is_bound:
                latest_quote = quotes_qs.first()
                if latest_quote is not None:
                    self.fields["quote"].initial = latest_quote
                    self.fields["amount"].initial = latest_quote.total_amount
                    self.fields["currency"].initial = latest_quote.currency
        else:
            self.fields["quote"].queryset = FeeQuote.objects.none()

        self.fields["quote"].required = False

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount <= Decimal("0.00"):
            raise forms.ValidationError("Payment amount must be greater than zero.")
        return amount

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        payment_date = cleaned_data.get("payment_date")

        if status == PaymentRecord.Status.PAID and payment_date is None:
            cleaned_data["payment_date"] = timezone.localdate()
        return cleaned_data


class SecretariatQuickAddMemberForm(forms.Form):
    username = forms.CharField(max_length=150, required=True, label="Username")
    email = forms.EmailField(required=True, label="Email address (synthetic)")
    first_name = forms.CharField(max_length=150, required=True, label="First name")
    last_name = forms.CharField(max_length=150, required=True, label="Last name")
    member_type = forms.ChoiceField(
        choices=MemberProfile.MemberType.choices,
        initial=MemberProfile.MemberType.HUNTER,
        label="Membership category",
    )
    status = forms.ChoiceField(
        choices=MemberProfile.Status.choices,
        initial=MemberProfile.Status.APPLICANT,
        label="Initial status",
    )
    phone = forms.CharField(max_length=40, required=True, label="Phone")
    street_address = forms.CharField(max_length=255, required=True, label="Street address")
    city = forms.CharField(max_length=120, required=True, label="City")
    postal_code = forms.CharField(max_length=20, required=True, label="Postal code")
    hunting_licence_number = forms.CharField(
        max_length=64,
        required=False,
        label="Hunting licence number (optional)",
    )
    licence_valid_until = forms.DateField(
        required=False,
        label="Licence valid until",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    insurance_valid_until = forms.DateField(
        required=False,
        label="Insurance valid until",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    valid_from = forms.DateField(
        required=False,
        label="Membership valid from",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    valid_until = forms.DateField(
        required=False,
        label="Membership valid until",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    include_insurance = forms.BooleanField(
        required=False,
        initial=False,
        label="Include insurance add-on in initial fee quote",
    )
    apply_reduced_rate = forms.BooleanField(
        required=False,
        initial=False,
        label="Apply reduced-rate discount in initial fee quote",
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with this username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        licence_valid_until = cleaned_data.get("licence_valid_until")
        licence_number = (cleaned_data.get("hunting_licence_number") or "").strip()
        valid_from = cleaned_data.get("valid_from")
        valid_until = cleaned_data.get("valid_until")

        if licence_valid_until and not licence_number:
            self.add_error(
                "hunting_licence_number",
                "Please provide a hunting licence number when specifying a licence expiry date.",
            )

        if valid_from and valid_until and valid_until < valid_from:
            self.add_error(
                "valid_until",
                "Valid-until date cannot be earlier than the valid-from date.",
            )
        return cleaned_data