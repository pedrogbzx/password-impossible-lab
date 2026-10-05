import hmac
import re
import secrets
import sqlite3
from functools import wraps

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

from config import address, load_config, private_address, validate_config
from lab.database import connect, init_db, list_users, reset_db
from lab.hashing import hash_password, verify_password
from lab.models import VERSIONS


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.update(load_config())
    if overrides:
        app.config.update(overrides)
    validate_config(app.config)
    init_db(app.config['DATABASE'])

    def csrf_token():
        if 'csrf' not in session:
            session['csrf'] = secrets.token_hex(32)
        return session['csrf']

    app.jinja_env.globals.update(csrf_token=csrf_token, versions=VERSIONS)

    @app.before_request
    def boundaries():
        peer = address(request.remote_addr or '')
        if peer is None or not private_address(str(peer)):
            abort(403)
        if not app.config['LAB_LAN_MODE'] and not peer.is_loopback:
            abort(403)
        # Host allowlist also blocks ordinary DNS rebinding. No forwarded headers trusted.
        allowed = {'127.0.0.1', 'localhost', '[::1]', app.config['HOST'], f"[{app.config['HOST']}]"}
        host = request.host.lower()
        if host.startswith('['):
            hostname = host.split(']')[0] + ']'
        else:
            hostname = host.split(':')[0]
        if hostname not in allowed:
            abort(400)
        if request.method == 'POST':
            expected = session.get('csrf', '')
            actual = request.form.get('csrf_token', '')
            if not expected or not hmac.compare_digest(expected.encode('utf-8'), actual.encode('utf-8')):
                abort(400, 'Token CSRF inválido. Recarga el formulario.')

    @app.after_request
    def headers(response):
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"
        return response

    def local_admin(function):
        @wraps(function)
        def wrapped(*args, **kwargs):
            peer = address(request.remote_addr or '')
            if not peer or not peer.is_loopback:
                abort(403, 'Herramienta administrativa disponible solo desde loopback.')
            return function(*args, **kwargs)
        return wrapped

    @app.get('/')
    def index():
        return redirect(url_for('lab_dashboard'))

    @app.get('/lab')
    def lab_dashboard():
        return render_template('lab.html', active='lab', lan=app.config['LAB_LAN_MODE'])

    @app.route('/<version>', methods=['GET', 'POST'])
    def version_page(version):
        if version not in VERSIONS:
            abort(404)
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            action = request.form.get('action')
            if not re.fullmatch(r'[A-Za-z0-9_.-]{3,32}', username) or not 1 <= len(password) <= 256:
                flash('Usa un alias de 3–32 caracteres (letras ASCII, números, _, . o -) y una contraseña de 1–256 caracteres.', 'error')
            elif action == 'register':
                try:
                    encoded = hash_password(version, password, app.config)
                    with connect(app.config['DATABASE']) as db:
                        cursor = db.execute('INSERT INTO users(username,password_hash,version) VALUES(?,?,?)', (username, encoded, version))
                        user_id = cursor.lastrowid
                    session[f'user_{version}'] = user_id
                    flash('Cuenta ficticia creada. SQLite conserva únicamente el hash.', 'success')
                except (ValueError, sqlite3.IntegrityError) as exc:
                    flash(str(exc) if isinstance(exc, ValueError) else 'Ese alias ya existe en esta versión.', 'error')
            elif action == 'login':
                with connect(app.config['DATABASE']) as db:
                    user = db.execute('SELECT * FROM users WHERE username=? AND version=?', (username, version)).fetchone()
                if user and verify_password(version, user['password_hash'], password, app.config):
                    session[f'user_{version}'] = user['id']
                    flash('Sesión iniciada en el laboratorio.', 'success')
                else:
                    flash('Alias o contraseña incorrectos.', 'error')
            else:
                abort(400)
            return redirect(url_for('version_page', version=version))
        with connect(app.config['DATABASE']) as db:
            user = db.execute('SELECT username FROM users WHERE id=? AND version=?', (session.get(f'user_{version}'), version)).fetchone()
        return render_template('social.html' if user else 'login.html', active=version, version=version,
                               info=VERSIONS[version], user=user, params=app.config)

    @app.post('/logout/<version>')
    def logout(version):
        if version not in VERSIONS:
            abort(404)
        session.pop(f'user_{version}', None)
        return redirect(url_for('version_page', version=version))

    @app.get('/database-viewer')
    @local_admin
    def database_viewer():
        with connect(app.config['DATABASE']) as db:
            captures = db.execute('SELECT * FROM captures ORDER BY id').fetchall() if app.config['LAB_CAPTURE_MODE'] else []
            count = db.execute('SELECT count(*) FROM captures').fetchone()[0]
        return render_template('database.html', active='database', users=list_users(app.config['DATABASE']), captures=captures, count=count)

    @app.route('/reset', methods=['GET', 'POST'])
    @local_admin
    def reset():
        if request.method == 'POST':
            if request.form.get('confirmation') != 'RESET':
                flash('Escribe RESET para confirmar.', 'error')
            else:
                reset_db(app.config['DATABASE'])
                # Rotate key to invalidate every previous browser session, not just this one.
                app.secret_key = secrets.token_hex(32)
                session.clear()
                flash('Laboratorio vacío. Usuarios, hashes y capturas eliminados.', 'success')
                return redirect(url_for('lab_dashboard'))
        return render_template('reset.html', active='reset')

    @app.route('/plot-twist', methods=['GET', 'POST'])
    @local_admin
    def plot_twist():
        if request.method == 'POST':
            if not app.config['LAB_CAPTURE_MODE']:
                abort(403, 'LAB_CAPTURE_MODE está deshabilitado.')
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            if request.form.get('fictional') != 'yes' or not re.fullmatch(r'[A-Za-z0-9_.-]{3,32}', username) or not 1 <= len(password) <= 256:
                flash('Confirma el uso de credenciales ficticias y completa los campos.', 'error')
            else:
                with connect(app.config['DATABASE']) as db:
                    db.execute('INSERT INTO captures(username,fictional_password) VALUES(?,?)', (username, password))
                flash('Demostración: el dato se guardó en claro en captures. No fue necesario crackearlo.', 'success')
            return redirect(url_for('plot_twist'))
        return render_template('plot_twist.html', active='twist', capture=app.config['LAB_CAPTURE_MODE'])

    return app


if __name__ == '__main__':
    from waitress import serve
    app = create_app()
    print(f"FaceLook LAB: http://{app.config['HOST']}:{app.config['PORT']}/lab", flush=True)
    print(f"LAN={app.config['LAB_LAN_MODE']} · CAPTURE={app.config['LAB_CAPTURE_MODE']} · sin debug", flush=True)
    host = app.config['HOST']
    bind = f'[{host}]' if ':' in host else host
    listeners = [f"{bind}:{app.config['PORT']}"]
    if not address(host).is_loopback:
        listeners.append(f"127.0.0.1:{app.config['PORT']}")
    serve(app, listen=' '.join(listeners), threads=4, max_request_body_size=16384)
