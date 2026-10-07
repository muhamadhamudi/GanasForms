# GANAS Forms

Platform formulir dan pendataan digital untuk **GANAS — Gerakan Anti Narkoba & HIV/AIDS, Universitas Nusa Putra**.

UI/UX mengikuti referensi Google Stitch yang diberikan: modern SaaS dashboard, Inter, navy/blue/red GANAS identity, Tailwind CSS, dan AOS.

## Fitur

- Guest landing page `/` hanya menampilkan formulir PUBLISHED yang sedang aktif.
- Dynamic form builder di `/admin`.
- Question types: Short Text, Long Text, Email, Number, Phone, Date, Dropdown, Multiple Choice, Checkboxes.
- Required validation dan server-side validation.
- Draft / Published / Closed / Archived.
- Deadline dan response limit.
- Admin dashboard.
- Response dashboard per form.
- Pagination.
- Detail response.
- Export Excel `.xlsx`, PDF, dan CSV.
- Duplicate form tanpa menyalin response.
- CSRF protection.
- Flask-Login + password hashing.
- SQLite.
- Responsive mobile-first.
- Tailwind CSS CDN.
- AOS animation.
- PythonAnywhere-friendly.

## Struktur

```text
ganas-forms/
├── app/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── templates/
│   └── static/
├── instance/
├── tests/
├── config.py
├── run.py
├── requirements.txt
└── .env.example
```

## Jalankan di Ubuntu / Termux

```bash
cd ~/ai-coding/projects
unzip ganas-forms.zip
cd ganas-forms

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

Generate secret key yang lebih kuat untuk production:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Masukkan hasilnya ke `SECRET_KEY` di `.env`.

Inisialisasi:

```bash
flask --app run.py init-db
flask --app run.py create-admin
```

Jalankan:

```bash
python run.py
```

Buka:

```text
http://127.0.0.1:5000
```

Admin:

```text
http://127.0.0.1:5000/admin
```

## Network di perangkat lain

Untuk akses dari perangkat lain dalam jaringan yang sama, jalankan:

```bash
python run.py
```

Cari IP perangkat:

```bash
ip addr
```

Kemudian akses:

```text
http://IP-UBUNTU:5000
```

## Testing

```bash
pytest -q
```

## PythonAnywhere

1. Upload project.
2. Buat virtualenv Python yang kompatibel.
3. `pip install -r requirements.txt`
4. Atur `SECRET_KEY` sebagai environment variable.
5. Pastikan SQLite berada di lokasi yang writable.
6. Arahkan WSGI ke object `app` dari `run.py`.
7. Jalankan `flask --app run.py init-db`.
8. Buat admin dengan `flask --app run.py create-admin`.

Jangan menggunakan development server `python run.py` sebagai server production PythonAnywhere.

## Catatan

Tailwind CSS dan AOS menggunakan CDN pada MVP agar setup ringan. Jika production membutuhkan asset bundling, keduanya dapat dipindahkan ke asset build lokal tanpa mengubah arsitektur Flask.

File `.env` dan database di `instance/` tidak boleh di-commit.
