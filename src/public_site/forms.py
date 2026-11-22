from django import forms

from .models import MembershipEnquiry, VolunteerEnquiry


class VolunteerEnquiryForm(forms.ModelForm):
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "tabindex": "-1",
                "autocomplete": "off",
                "aria-hidden": "true",
            }
        ),
        label="Website",
    )

    consent_given = forms.BooleanField(
        required=True,
        label="Súhlasím so spracovaním poskytnutých osobných údajov na účely kontaktovania v súvislosti s dobrovoľníckou činnosťou asociácie.",
        error_messages={
            "required": "Pre odoslanie prihlášky je potrebný váš súhlas so spracovaním osobných údajov."
        },
    )

    class Meta:
        model = VolunteerEnquiry
        fields = [
            "full_name",
            "region",
            "email",
            "phone",
            "interests",
            "message",
            "consent_given",
        ]
        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "placeholder": "Napr. Ján Novák",
                    "class": "w-full rounded-lg border border-stone-300 px-3.5 py-2.5 text-stone-900 focus:border-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-700/20",
                }
            ),
            "region": forms.TextInput(
                attrs={
                    "placeholder": "Napr. Nitriansky kraj / Okres Nitra",
                    "class": "w-full rounded-lg border border-stone-300 px-3.5 py-2.5 text-stone-900 focus:border-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-700/20",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "jan.novak@example.sk",
                    "class": "w-full rounded-lg border border-stone-300 px-3.5 py-2.5 text-stone-900 focus:border-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-700/20",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "placeholder": "+421 900 123 456 (nepovinné)",
                    "class": "w-full rounded-lg border border-stone-300 px-3.5 py-2.5 text-stone-900 focus:border-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-700/20",
                }
            ),
            "interests": forms.TextInput(
                attrs={
                    "placeholder": "Napr. Ochrana prírody, práca s mládežou, organizácia podujatí",
                    "class": "w-full rounded-lg border border-stone-300 px-3.5 py-2.5 text-stone-900 focus:border-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-700/20",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Napíšte nám krátko, ako by ste sa chceli zapojiť...",
                    "class": "w-full rounded-lg border border-stone-300 px-3.5 py-2.5 text-stone-900 focus:border-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-700/20",
                }
            ),
        }

    def clean_website(self):
        value = self.cleaned_data.get("website", "")
        if value:
            raise forms.ValidationError("Spam submission detected.")
        return value


class MembershipEnquiryForm(forms.ModelForm):
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "tabindex": "-1",
                "autocomplete": "off",
                "aria-hidden": "true",
            }
        ),
        label="Website",
    )

    consent_given = forms.BooleanField(
        required=True,
        label="Súhlasím so spracovaním poskytnutých osobných údajov na účely poskytnutia informácií o členstve v asociácii.",
        error_messages={
            "required": "Pre odoslanie dopytu je potrebný váš súhlas so spracovaním osobných údajov."
        },
    )

    class Meta:
        model = MembershipEnquiry
        fields = [
            "full_name",
            "email",
            "phone",
            "region",
            "preferred_membership_type",
            "has_hunting_licence",
            "message",
            "consent_given",
        ]
        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "placeholder": "Napr. Peter Horváth",
                    "class": "w-full rounded-lg border border-stone-300 px-3.5 py-2.5 text-stone-900 focus:border-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-700/20",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "placeholder": "peter.horvath@example.sk",
                    "class": "w-full rounded-lg border border-stone-300 px-3.5 py-2.5 text-stone-900 focus:border-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-700/20",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "placeholder": "+421 900 123 456 (nepovinné)",
                    "class": "w-full rounded-lg border border-stone-300 px-3.5 py-2.5 text-stone-900 focus:border-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-700/20",
                }
            ),
            "region": forms.TextInput(
                attrs={
                    "placeholder": "Napr. Trnavský kraj / Okres Senica",
                    "class": "w-full rounded-lg border border-stone-300 px-3.5 py-2.5 text-stone-900 focus:border-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-700/20",
                }
            ),
            "preferred_membership_type": forms.Select(
                attrs={
                    "class": "w-full rounded-lg border border-stone-300 bg-white px-3.5 py-2.5 text-stone-900 focus:border-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-700/20",
                }
            ),
            "has_hunting_licence": forms.CheckboxInput(
                attrs={
                    "class": "h-4 w-4 rounded border-stone-300 text-emerald-700 focus:ring-emerald-700",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Napíšte nám svoju otázku k podmienkam vstupu, členským poplatkom alebo skúškam...",
                    "class": "w-full rounded-lg border border-stone-300 px-3.5 py-2.5 text-stone-900 focus:border-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-700/20",
                }
            ),
        }

    def clean_website(self):
        value = self.cleaned_data.get("website", "")
        if value:
            raise forms.ValidationError("Spam submission detected.")
        return value