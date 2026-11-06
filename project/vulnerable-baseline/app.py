"""Deliberately vulnerable local-only reference. Never deploy."""
import os, sqlite3
from flask import Flask, request, session, render_template_string, send_file, abort
app=Flask(__name__); app.secret_key='dev-secret'
DB=os.environ.get('NOTES_DB','/tmp/nv-vuln.db')
def conn():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
 c.executescript("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,username TEXT,password TEXT,role TEXT); CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY,owner_id INTEGER,title TEXT,body TEXT);")
 if not c.execute("SELECT 1 FROM users WHERE username='admin'").fetchone(): c.execute("INSERT INTO users(username,password,role) VALUES('admin','admin123','admin')")
 c.commit(); return c
@app.get('/login')
def login():
 u=request.args.get('u',''); p=request.args.get('p',''); row=conn().execute("SELECT * FROM users WHERE username='%s' AND password='%s'"%(u,p)).fetchone()
 if row: session['uid']=row['id']; session['role']=row['role']
 return 'logged in' if row else 'invalid', (200 if row else 401)
@app.get('/search')
def search():
 q=request.args.get('q',''); rows=conn().execute("SELECT * FROM notes WHERE title LIKE '%%%s%%'"%q).fetchall(); return '<br>'.join(x['title'] for x in rows)
@app.route('/note',methods=['GET','POST'])
def create_note():
 if request.method=='POST':
  owner=request.form.get('owner_id','1'); title=request.form.get('title',''); body=request.form.get('body','')
  conn().execute("INSERT INTO notes(owner_id,title,body) VALUES(%s,'%s','%s')"%(owner,title,body)); conn().commit(); return 'saved'
 return '<form method=post><input name=owner_id><input name=title><textarea name=body></textarea></form>'
@app.get('/note/<int:nid>')
def note(nid):
 row=conn().execute('SELECT * FROM notes WHERE id=?',(nid,)).fetchone()
 if not row: abort(404)
 return render_template_string('<h1>'+row['title']+'</h1><p>'+row['body']+'</p>')
@app.get('/export/<int:nid>')
def export(nid):
 row=conn().execute('SELECT * FROM notes WHERE id=?',(nid,)).fetchone()
 return row['body'] if row else ('missing',404)
@app.get('/admin')
def admin():
 if session.get('role')!='admin': abort(403)
 return str([dict(r) for r in conn().execute('SELECT * FROM users')])
@app.get('/register')
def register():
 u=request.args.get('u',''); p=request.args.get('p',''); conn().execute("INSERT INTO users(username,password,role) VALUES('%s','%s','user')"%(u,p)); return 'registered'
if __name__=='__main__': app.run('0.0.0.0',8080)
