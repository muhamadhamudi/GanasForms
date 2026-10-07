from ..extensions import db

class Response(db.Model):
    __tablename__ = "responses"
    id = db.Column(db.Integer, primary_key=True)
    form_id = db.Column(db.Integer, db.ForeignKey("forms.id"), nullable=False, index=True)
    submitted_at = db.Column(db.DateTime, server_default=db.func.now(), index=True)
    form = db.relationship("Form", back_populates="responses")
    answers = db.relationship("ResponseAnswer", back_populates="response", cascade="all, delete-orphan")

class ResponseAnswer(db.Model):
    __tablename__ = "response_answers"
    id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(db.Integer, db.ForeignKey("responses.id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("form_questions.id"), nullable=False, index=True)
    answer = db.Column(db.Text, default="")
    response = db.relationship("Response", back_populates="answers")
    question = db.relationship("FormQuestion", back_populates="answers")
