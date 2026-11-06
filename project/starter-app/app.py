import os, re, secrets, sqlite3, time
from functools import wraps
from pathlib import Path
from flask import Flask, abort, flash, g, redirect, render_template, request, send_file, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE = Path(__file__).resolve().parent
DB = Path(os.environ.get("NOTES_DB", BASE / "instance" / "notes.db"))
TEAM_ID = os.environ.get("TEAM_ID", "local-team")
app = Flask(__name__)
if not os.environ.get('SECRET_KEY') or not os.environ.get('ADMIN_PASSWORD'):
    raise RuntimeError('Set SECRET_KEY and ADMIN_PASSWORD before starting NoteVault')
app.config.update(SECRET_KEY=os.environ['SECRET_KEY'], SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "0") == "1", MAX_CONTENT_LENGTH=1_048_576)

SCHEMA = """CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user'); CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, owner_id INTEGER NOT NULL REFERENCES users(id), title TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);"""
def db():
    if "db" not in g:
        DB.parent.mkdir(parents=True, exist_ok=True)
        g.db=sqlite3.connect(DB); g.db.row_factory=sqlite3.Row; g.db.execute("PRAGMA foreign_keys=ON"); g.db.executescript(SCHEMA); g.db.commit()
        if not g.db.execute("SELECT 1 FROM users WHERE username='admin'").fetchone(): g.db.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)", ('admin',generate_password_hash(os.environ['ADMIN_PASSWORD']),'admin')); g.db.commit()
    return g.db
@app.teardown_appcontext
def close_db(exc):
    c=g.pop('db',None)
    if c: c.close()
def login_required(fn):
    @wraps(fn)
    def wrapped(*a,**kw):
        if not session.get('uid'): return redirect(url_for('login'))
        return fn(*a,**kw)
    return wrapped
def admin_required(fn):
    @wraps(fn)
    def wrapped(*a,**kw):
        if not session.get('uid'): return redirect(url_for('login'))
        if session.get('role')!='admin': abort(403)
        return fn(*a,**kw)
    return wrapped
def csrf_ok(): return secrets.compare_digest(session.get('csrf',''), request.form.get('csrf',''))
def csrf_field():
    if 'csrf' not in session: session['csrf']=secrets.token_urlsafe(32)
    return session['csrf']
app.jinja_env.globals['csrf_token']=csrf_field

def valid_name(value): return bool(re.fullmatch(r'[A-Za-z0-9_.-]{3,32}', value or ''))
def valid_text(value, limit): return isinstance(value,str) and 1 <= len(value.strip()) <= limit
@app.get('/')
def index():
    if not session.get('uid'): return redirect(url_for('login'))
    notes=db().execute('SELECT id,title,body,created_at FROM notes WHERE owner_id=? ORDER BY id DESC',(session['uid'],)).fetchall()
    return render_template('index.html', notes=notes, team=TEAM_ID)
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        if not csrf_ok(): abort(400)
        name=request.form.get('username','').strip(); pw=request.form.get('password','')
        if not valid_name(name) or len(pw)<12: flash('Username must be 3–32 safe characters; password must be at least 12 characters.'); return render_template('register.html')
        try: db().execute('INSERT INTO users(username,password_hash) VALUES(?,?)',(name,generate_password_hash(pw))); db().commit()
        except sqlite3.IntegrityError: flash('Username unavailable.'); return render_template('register.html')
        return redirect(url_for('login'))
    return render_template('register.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        if not csrf_ok(): abort(400)
        row=db().execute('SELECT * FROM users WHERE username=?',(request.form.get('username',''),)).fetchone()
        if not row or not check_password_hash(row['password_hash'],request.form.get('password','')): flash('Invalid credentials.'); return render_template('login.html'),401
        session.clear(); session['uid']=row['id']; session['role']=row['role']; session['csrf']=secrets.token_urlsafe(32)
        return redirect(url_for('index'))
    return render_template('login.html')
@app.post('/logout')
@login_required
def logout():
    if not csrf_ok(): abort(400)
    session.clear(); return redirect(url_for('login'))
@app.post('/notes')
@login_required
def create_note():
    if not csrf_ok(): abort(400)
    title=request.form.get('title',''); body=request.form.get('body','')
    if not valid_text(title,120) or not valid_text(body,10000): abort(400)
    db().execute('INSERT INTO notes(owner_id,title,body) VALUES(?,?,?)',(session['uid'],title.strip(),body.strip())); db().commit(); return redirect(url_for('index'))
@app.get('/search')
@login_required
def search():
    q=request.args.get('q','')[:100]
    rows=db().execute("SELECT id,title,body FROM notes WHERE owner_id=? AND (title LIKE ? ESCAPE '\\' OR body LIKE ? ESCAPE '\\') ORDER BY id DESC",(session['uid'],f'%{q}%',f'%{q}%')).fetchall()
    return render_template('search.html',q=q,notes=rows)
@app.get('/admin')
@admin_required
def admin():
    users=db().execute('SELECT id,username,role FROM users ORDER BY id').fetchall()
    return render_template('admin.html', users=users, count=db().execute('SELECT COUNT(*) FROM notes').fetchone()[0])
@app.get('/export/<int:note_id>')
@login_required
def export_note(note_id):
    note=db().execute('SELECT id,title,body FROM notes WHERE id=? AND owner_id=?',(note_id,session['uid'])).fetchone()
    if not note: abort(404)
    from io import BytesIO
    from reportlab.pdfgen import canvas
    output=BytesIO(); p=canvas.Canvas(output); p.drawString(72,760,note['title'][:120]); y=735
    for line in note['body'].splitlines()[:45]: p.drawString(72,y,line[:110]); y-=14
    p.showPage(); p.save(); output.seek(0); return send_file(output,mimetype='application/pdf',as_attachment=True,download_name='note.pdf')
@app.get('/health')
def health(): return {'status':'ok'}
if __name__=='__main__': app.run(host='0.0.0.0',port=8080)
