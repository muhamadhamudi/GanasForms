from app.models import Form, FormQuestion
from app.extensions import db

def login(client):
    return client.post("/login", data={"identity":"admin","password":"password"}, follow_redirects=True)

def test_home(client):
    assert client.get("/").status_code == 200

def test_admin_requires_login(client):
    r = client.get("/admin")
    assert r.status_code == 302
    assert "/login" in r.location

def test_login(client):
    r = login(client)
    assert r.status_code == 200
    assert b"Selamat datang" in r.data

def test_draft_not_public(client, app):
    with app.app_context():
        f=Form(title="Draft",slug="draft",status="DRAFT")
        db.session.add(f); db.session.commit()
    assert b"Draft" not in client.get("/").data

def test_create_publish_submit(client, app):
    login(client)
    import json
    payload=[{"label":"Nama","type":"short_text","required":True,"description":"","placeholder":"","options":[]}]
    r=client.post("/admin/forms/create",data={"title":"Pendaftaran Test","description":"Test","questions_json":json.dumps(payload),"action":"published"},follow_redirects=True)
    assert r.status_code==200
    with app.app_context():
        f=Form.query.filter_by(slug="pendaftaran-test").first()
        assert f.status=="PUBLISHED"
        fid=f.id; qid=f.questions[0].id
    r=client.post("/form/pendaftaran-test",data={f"q_{qid}":"Muhamad"},follow_redirects=True)
    assert r.status_code==200
    assert b"Terima Kasih" in r.data
    with app.app_context():
        f=Form.query.get(fid)
        assert len(f.responses)==1
