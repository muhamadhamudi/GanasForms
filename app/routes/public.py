from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from ..extensions import db
from ..models import Form, Response, ResponseAnswer
from ..services.form_service import form_is_open

public_bp = Blueprint("public", __name__)

@public_bp.get("/")
def home():
    forms = Form.query.filter_by(status="PUBLISHED").order_by(Form.created_at.desc()).all()
    active = [f for f in forms if form_is_open(f)]
    return render_template("public/home.html", forms=active)

@public_bp.route("/form/<slug>", methods=["GET","POST"])
def fill_form(slug):
    form = Form.query.filter_by(slug=slug).first_or_404()
    if not form_is_open(form):
        return render_template("public/closed.html", form=form)
    if request.method == "POST":
        response = Response(form=form)
        db.session.add(response)
        db.session.flush()
        for q in form.questions:
            values = request.form.getlist(f"q_{q.id}")
            answer = ", ".join(v.strip() for v in values if v.strip())
            if q.required and not answer:
                db.session.rollback()
                flash(f'"{q.label}" wajib diisi.', "error")
                return render_template("public/form.html", form=form)
            if q.type == "email" and answer and ("@" not in answer or "." not in answer.split("@")[-1]):
                db.session.rollback()
                flash(f'"{q.label}" harus menggunakan email yang valid.', "error")
                return render_template("public/form.html", form=form)
            if q.type == "number" and answer:
                try: float(answer)
                except ValueError:
                    db.session.rollback()
                    flash(f'"{q.label}" harus berupa angka.', "error")
                    return render_template("public/form.html", form=form)
            allowed = {o.value for o in q.options}
            if q.options and any(v not in allowed for v in values):
                db.session.rollback()
                abort(400)
            db.session.add(ResponseAnswer(response=response, question=q, answer=answer))
        db.session.commit()
        return render_template("public/success.html", form=form)
    return render_template("public/form.html", form=form)
