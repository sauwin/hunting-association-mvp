from django import forms

from .models import MemberProfile
from .services import DEFAULT_CONSENT_TEXT


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