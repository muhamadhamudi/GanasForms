import json

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Response as FlaskResponse,
    abort,
)

from flask_login import login_required, current_user

from ..extensions import db
from ..models import (
    Form,
    FormQuestion,
    FormOption,
    Response as FormResponse,
)
from ..services.form_service import (
    unique_slug,
    parse_datetime,
    question_types,
)
from ..services.export_service import (
    xlsx_bytes,
    pdf_bytes,
    csv_text,
)


admin_bp = Blueprint("admin", __name__)


# =========================================================
# ADMIN PROTECTION
# =========================================================

@admin_bp.before_request
@login_required
def protect():
    pass


# =========================================================
# HELPERS
# =========================================================

def parse_response_limit(value):
    """
    Mengubah response_limit menjadi integer yang aman.

    Empty -> None
    Invalid -> ValueError
    """

    value = (value or "").strip()

    if not value:
        return None

    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValueError(
            "Batas respons harus berupa angka."
        )

    if number < 1:
        raise ValueError(
            "Batas respons minimal adalah 1."
        )

    return number


def parse_questions_payload(payload):
    """
    Parse questions_json dari form builder.
    Selalu mengembalikan list.
    """

    if not payload:
        return []

    try:
        data = json.loads(payload)
    except (TypeError, ValueError, json.JSONDecodeError):
        raise ValueError(
            "Data pertanyaan tidak valid."
        )

    if not isinstance(data, list):
        raise ValueError(
            "Format data pertanyaan tidak valid."
        )

    return data


def save_questions(form, payload=None):
    """
    Menyimpan pertanyaan dan pilihan dari form builder.
    """

    if payload is None:
        payload = request.form.get(
            "questions_json",
            "[]"
        )

    questions = parse_questions_payload(payload)

    for index, item in enumerate(questions):

        if not isinstance(item, dict):
            continue

        question_type = str(
            item.get("type", "short_text")
        ).strip() or "short_text"

        label = str(
            item.get("label", "")
        ).strip()

        # Jangan membuat question tanpa label
        if not label:
            continue

        description = str(
            item.get("description", "")
        ).strip()

        placeholder = str(
            item.get("placeholder", "")
        ).strip()

        # Jangan gunakan bool("false") karena hasilnya True
        required_value = item.get("required", False)

        if isinstance(required_value, str):
            required = required_value.lower() in (
                "true",
                "1",
                "yes",
                "on",
            )
        else:
            required = bool(required_value)

        question = FormQuestion(
            form=form,
            type=question_type,
            label=label,
            description=description,
            placeholder=placeholder,
            required=required,
            sort_order=index,
        )

        db.session.add(question)

        # Flush supaya question.id tersedia
        db.session.flush()

        options = item.get("options") or []

        if not isinstance(options, list):
            continue

        for option_index, option in enumerate(options):

            if not isinstance(option, dict):
                continue

            option_label = str(
                option.get("label", "")
            ).strip()

            if not option_label:
                continue

            option_value = str(
                option.get("value")
                or option_label
            ).strip()

            db.session.add(
                FormOption(
                    question=question,
                    label=option_label,
                    value=option_value,
                    sort_order=option_index,
                )
            )


def delete_form_questions(form):
    """
    Menghapus seluruh question form.

    Karena FormQuestion.options dan FormQuestion.answers
    menggunakan cascade delete-orphan, child data ikut
    dihapus.
    """

    for question in list(form.questions):
        db.session.delete(question)

    db.session.flush()


# =========================================================
# DASHBOARD
# =========================================================

@admin_bp.get("")
def dashboard():

    forms = (
        Form.query
        .order_by(Form.created_at.desc())
        .all()
    )

    responses = (
        FormResponse.query
        .order_by(FormResponse.submitted_at.desc())
        .limit(8)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        forms=forms,
        recent_responses=responses,
    )


# =========================================================
# FORM LIST
# =========================================================

@admin_bp.get("/forms")
def forms():

    status = request.args.get(
        "status",
        "ALL"
    ).upper()

    query = (
        Form.query
        .order_by(Form.created_at.desc())
    )

    allowed_statuses = {
        "ALL",
        "DRAFT",
        "PUBLISHED",
        "CLOSED",
        "ARCHIVED",
    }

    if status not in allowed_statuses:
        status = "ALL"

    if status != "ALL":
        query = query.filter_by(
            status=status
        )

    return render_template(
        "admin/forms.html",
        forms=query.all(),
        active_status=status,
    )


# =========================================================
# CREATE FORM
# =========================================================

@admin_bp.route(
    "/forms/create",
    methods=["GET", "POST"]
)
def create_form():

    if request.method == "GET":

        return render_template(
            "admin/form_builder.html",
            form=None,
            types=question_types(),
        )

    try:

        title = request.form.get(
            "title",
            ""
        ).strip()

        if not title:
            flash(
                "Judul formulir wajib diisi.",
                "error",
            )

            return render_template(
                "admin/form_builder.html",
                form=None,
                types=question_types(),
            )

        description = request.form.get(
            "description",
            ""
        ).strip()

        deadline_raw = request.form.get(
            "deadline"
        )

        deadline = parse_datetime(
            deadline_raw
        ) if deadline_raw else None

        response_limit = parse_response_limit(
            request.form.get(
                "response_limit"
            )
        )

        success_message = (
            request.form.get(
                "success_message"
            )
            or "Respons kamu berhasil dikirim."
        ).strip()

        action = (
            request.form.get(
                "action",
                "draft"
            )
            .lower()
        )

        if action not in (
            "draft",
            "published",
        ):
            action = "draft"

        form = Form(
            title=title,
            description=description,
            slug=unique_slug(title),
            creator=current_user,
            deadline=deadline,
            response_limit=response_limit,
            success_message=success_message,
            status=action.upper(),
        )

        db.session.add(form)

        db.session.flush()

        save_questions(form)

        db.session.commit()

        flash(
            "Formulir berhasil dibuat.",
            "success",
        )

        return redirect(
            url_for(
                "admin.form_detail",
                form_id=form.id,
            )
        )

    except ValueError as exc:

        db.session.rollback()

        flash(
            str(exc),
            "error",
        )

        return render_template(
            "admin/form_builder.html",
            form=None,
            types=question_types(),
        )

    except Exception:

        db.session.rollback()

        flash(
            "Terjadi kesalahan saat membuat formulir. "
            "Periksa kembali data yang dimasukkan.",
            "error",
        )

        return render_template(
            "admin/form_builder.html",
            form=None,
            types=question_types(),
        )


# =========================================================
# EDIT FORM
# =========================================================

@admin_bp.route(
    "/forms/<int:form_id>/edit",
    methods=["GET", "POST"]
)
def edit_form(form_id):

    form = Form.query.get_or_404(
        form_id
    )

    if request.method == "GET":

        return render_template(
            "admin/form_builder.html",
            form=form,
            types=question_types(),
        )

    try:

        title = request.form.get(
            "title",
            ""
        ).strip()

        if not title:
            flash(
                "Judul formulir wajib diisi.",
                "error",
            )

            return render_template(
                "admin/form_builder.html",
                form=form,
                types=question_types(),
            )

        deadline_raw = request.form.get(
            "deadline"
        )

        deadline = parse_datetime(
            deadline_raw
        ) if deadline_raw else None

        response_limit = parse_response_limit(
            request.form.get(
                "response_limit"
            )
        )

        success_message = (
            request.form.get(
                "success_message"
            )
            or "Respons kamu berhasil dikirim."
        ).strip()

        action = (
            request.form.get(
                "action"
            )
            or form.status.lower()
        ).lower()

        allowed_actions = {
            "draft",
            "published",
            "closed",
            "archived",
        }

        if action not in allowed_actions:
            action = "draft"

        # Update informasi form
        form.title = title
        form.description = request.form.get(
            "description",
            ""
        ).strip()

        form.deadline = deadline
        form.response_limit = response_limit
        form.success_message = success_message
        form.status = action.upper()

        # =================================================
        # HAPUS QUESTION LAMA
        # =================================================
        #
        # Karena:
        #
        # Form.questions
        #     cascade all, delete-orphan
        #
        # FormQuestion.options
        #     cascade all, delete-orphan
        #
        # FormQuestion.answers
        #     cascade all, delete-orphan
        #
        # maka child data ikut dibersihkan.
        #

        delete_form_questions(form)

        # =================================================
        # SIMPAN QUESTION BARU
        # =================================================

        save_questions(form)

        db.session.commit()

        flash(
            "Formulir berhasil diperbarui.",
            "success",
        )

        return redirect(
            url_for(
                "admin.form_detail",
                form_id=form.id,
            )
        )

    except ValueError as exc:

        db.session.rollback()

        flash(
            str(exc),
            "error",
        )

        return render_template(
            "admin/form_builder.html",
            form=form,
            types=question_types(),
        )

    except Exception as exc:

        db.session.rollback()

        flash(
            "Gagal menyimpan perubahan formulir. "
            "Tidak ada perubahan yang disimpan.",
            "error",
        )

        return render_template(
            "admin/form_builder.html",
            form=form,
            types=question_types(),
        )


# =========================================================
# FORM DETAIL
# =========================================================

@admin_bp.get(
    "/forms/<int:form_id>"
)
def form_detail(form_id):

    form = Form.query.get_or_404(
        form_id
    )

    return render_template(
        "admin/form_detail.html",
        form=form,
    )


# =========================================================
# RESPONSES
# =========================================================

@admin_bp.get(
    "/forms/<int:form_id>/responses"
)
def responses(form_id):

    form = Form.query.get_or_404(
        form_id
    )

    try:
        page = max(
            int(
                request.args.get(
                    "page",
                    1
                )
            ),
            1,
        )
    except (TypeError, ValueError):
        page = 1

    per_page = 20

    pagination = (
        FormResponse.query
        .filter_by(form_id=form.id)
        .order_by(
            FormResponse.submitted_at.desc()
        )
        .paginate(
            page=page,
            per_page=per_page,
            error_out=False,
        )
    )

    return render_template(
        "admin/responses.html",
        form=form,
        pagination=pagination,
    )


# =========================================================
# RESPONSE DETAIL
# =========================================================

@admin_bp.get(
    "/forms/<int:form_id>/responses/<int:response_id>"
)
def response_detail(
    form_id,
    response_id,
):

    form = Form.query.get_or_404(
        form_id
    )

    response = (
        FormResponse.query
        .filter_by(
            id=response_id,
            form_id=form.id,
        )
        .first_or_404()
    )

    return render_template(
        "admin/response_detail.html",
        form=form,
        response=response,
    )


# =========================================================
# EXPORT
# =========================================================

@admin_bp.get(
    "/forms/<int:form_id>/export/<fmt>"
)
def export(form_id, fmt):

    form = Form.query.get_or_404(
        form_id
    )

    fmt = fmt.lower()

    if fmt == "xlsx":

        return FlaskResponse(
            xlsx_bytes(form),
            mimetype=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
            headers={
                "Content-Disposition":
                    f'attachment; '
                    f'filename="{form.slug}-responses.xlsx"'
            },
        )

    if fmt == "pdf":

        return FlaskResponse(
            pdf_bytes(form),
            mimetype="application/pdf",
            headers={
                "Content-Disposition":
                    f'attachment; '
                    f'filename="{form.slug}-responses.pdf"'
            },
        )

    if fmt == "csv":

        return FlaskResponse(
            csv_text(form),
            mimetype="text/csv; charset=utf-8",
            headers={
                "Content-Disposition":
                    f'attachment; '
                    f'filename="{form.slug}-responses.csv"'
            },
        )

    abort(404)


# =========================================================
# DUPLICATE FORM
# =========================================================

@admin_bp.post(
    "/forms/<int:form_id>/duplicate"
)
def duplicate(form_id):

    original = Form.query.get_or_404(
        form_id
    )

    try:

        copy = Form(
            title=f"{original.title} (Copy)",
            description=original.description,
            slug=unique_slug(
                f"{original.title}-copy"
            ),
            status="DRAFT",
            creator=current_user,
            deadline=original.deadline,
            response_limit=original.response_limit,
            allow_multiple=original.allow_multiple,
            success_message=original.success_message,
        )

        db.session.add(copy)

        db.session.flush()

        for question in original.questions:

            new_question = FormQuestion(
                form=copy,
                type=question.type,
                label=question.label,
                description=question.description,
                placeholder=question.placeholder,
                required=question.required,
                sort_order=question.sort_order,
            )

            db.session.add(
                new_question
            )

            db.session.flush()

            for option in question.options:

                db.session.add(
                    FormOption(
                        question=new_question,
                        label=option.label,
                        value=option.value,
                        sort_order=option.sort_order,
                    )
                )

        db.session.commit()

        flash(
            "Formulir berhasil diduplikasi sebagai draft.",
            "success",
        )

        return redirect(
            url_for(
                "admin.form_detail",
                form_id=copy.id,
            )
        )

    except Exception:

        db.session.rollback()

        flash(
            "Gagal menduplikasi formulir.",
            "error",
        )

        return redirect(
            url_for(
                "admin.form_detail",
                form_id=original.id,
            )
        )

# =========================================================
# DELETE FORM
# =========================================================
@admin_bp.post("/forms/<int:form_id>/delete")
def delete_form(form_id):
    form = Form.query.get_or_404(form_id)

    try:
        # Hapus response terlebih dahulu
        FormResponse.query.filter_by(
            form_id=form.id
        ).delete(
            synchronize_session=False
        )

        # Hapus semua question
        delete_form_questions(form)

        # Hapus form
        db.session.delete(form)

        db.session.commit()

        flash(
            "Formulir berhasil dihapus.",
            "success",
        )

    except Exception:
        db.session.rollback()

        flash(
            "Gagal menghapus formulir.",
            "error",
        )

    return redirect(
        url_for("admin.forms")
    )

# =========================================================
# CHANGE STATUS
# =========================================================

@admin_bp.post(
    "/forms/<int:form_id>/status/<status>"
)
def set_status(
    form_id,
    status,
):

    status = status.upper()

    allowed_statuses = {
        "DRAFT",
        "PUBLISHED",
        "CLOSED",
        "ARCHIVED",
    }

    if status not in allowed_statuses:
        abort(400)

    form = Form.query.get_or_404(
        form_id
    )

    try:

        form.status = status

        db.session.commit()

        flash(
            f"Status formulir menjadi {status}.",
            "success",
        )

    except Exception:

        db.session.rollback()

        flash(
            "Gagal mengubah status formulir.",
            "error",
        )

    return redirect(
        request.referrer
        or url_for("admin.forms")
    )