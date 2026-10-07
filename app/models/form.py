from ..extensions import db

class Form(db.Model):
    __tablename__ = "forms"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), default="DRAFT", nullable=False, index=True)
    deadline = db.Column(db.DateTime, nullable=True)
    response_limit = db.Column(db.Integer, nullable=True)
    allow_multiple = db.Column(db.Boolean, default=True, nullable=False)
    success_message = db.Column(db.Text, default="Respons kamu berhasil dikirim.")
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    creator = db.relationship("User", back_populates="forms")
    questions = db.relationship("FormQuestion", back_populates="form", cascade="all, delete-orphan", order_by="FormQuestion.sort_order")
    responses = db.relationship("Response", back_populates="form", cascade="all, delete-orphan")

class FormQuestion(db.Model):
    __tablename__ = "form_questions"
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey("forms.id"), nullable=False, index=True)
    type = db.Column(db.String(40), nullable=False, default="short_text")
    label = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, default="")
    placeholder = db.Column(db.String(300), default="")
    required = db.Column(db.Boolean, default=False, nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)

    form = db.relationship("Form", back_populates="questions")
    options = db.relationship("FormOption", back_populates="question", cascade="all, delete-orphan", order_by="FormOption.sort_order")
    answers = db.relationship(
    "ResponseAnswer",
    back_populates="question",
    cascade="all, delete-orphan"
)

class FormOption(db.Model):
    __tablename__ = "form_options"
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("form_questions.id"), nullable=False, index=True)
    label = db.Column(db.String(300), nullable=False)
    value = db.Column(db.String(300), nullable=False)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    question = db.relationship("FormQuestion", back_populates="options")
