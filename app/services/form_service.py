import re
from datetime import datetime
from ..extensions import db
from ..models import Form, FormQuestion, FormOption

def slugify(value):
    value = re.sub(r"[^a-zA-Z0-9\s-]", "", value).strip().lower()
    value = re.sub(r"[-\s]+", "-", value)
    return value or "formulir"

def unique_slug(title, current_id=None):
    base = slugify(title)
    slug, i = base, 2
    while True:
        q = Form.query.filter_by(slug=slug)
        if current_id:
            q = q.filter(Form.id != current_id)
        if not q.first():
            return slug
        slug = f"{base}-{i}"
        i += 1

def parse_datetime(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    return None

def form_is_open(form):
    if form.status != "PUBLISHED":
        return False
    if form.deadline and datetime.now() > form.deadline:
        return False
    if form.response_limit is not None and len(form.responses) >= form.response_limit:
        return False
    return True

def question_types():
    return {
        "short_text": "Short Text",
        "long_text": "Long Text",
        "email": "Email",
        "number": "Number",
        "phone": "Phone Number",
        "date": "Date",
        "dropdown": "Dropdown",
        "radio": "Multiple Choice",
        "checkbox": "Checkboxes",
    }
