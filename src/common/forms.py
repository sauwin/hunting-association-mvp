"""Shared form helpers used by several apps."""

from django import forms

# Same utility classes Student B puts on its inputs in public_site/forms.py,
# so that forms of both modules look identical.
INPUT_CLASSES = (
    "w-full rounded-lg border border-stone-300 bg-white px-3.5 py-2.5 text-stone-900 "
    "focus:border-emerald-700 focus:outline-none focus:ring-2 focus:ring-emerald-700/20"
)
CHECKBOX_CLASSES = "h-4 w-4 rounded border-stone-300 text-forest-600 focus:ring-forest-600"


class TailwindFormMixin:
    """Add Tailwind CSS classes to every widget of a form.

    Put it BEFORE the Django form class: ``class MyForm(TailwindFormMixin, forms.Form)``.
    Classes are added to the per-instance copy of each widget (Django deep-copies fields
    for every form instance), so nothing leaks between requests.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(
                widget,
                (forms.HiddenInput, forms.RadioSelect, forms.CheckboxSelectMultiple),
            ):
                continue
            css = CHECKBOX_CLASSES if isinstance(widget, forms.CheckboxInput) else INPUT_CLASSES
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} {css}".strip()
