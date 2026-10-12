"""Shared form helpers.

``StyledFormMixin`` applies the design-system input styling to every widget once,
so individual forms never repeat CSS classes.
"""

TEXT_INPUT_WIDGETS = {
    "TextInput",
    "EmailInput",
    "PasswordInput",
    "NumberInput",
    "URLInput",
    "DateInput",
    "DateTimeInput",
    "TimeInput",
    "Textarea",
    "Select",
}

INPUT_CLASS = (
    "w-full rounded-2xl border border-hairline bg-pure-white px-16 py-12 text-body "
    "text-ink-charcoal placeholder:text-steel-gray focus:border-electric-cobalt "
    "focus:outline-none focus:ring-1 focus:ring-electric-cobalt"
)


class StyledFormMixin:
    """Adds PortaTap input styling to all text-like widgets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if widget.__class__.__name__ in TEXT_INPUT_WIDGETS:
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} {INPUT_CLASS}".strip()
