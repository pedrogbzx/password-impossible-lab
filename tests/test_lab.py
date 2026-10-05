import hashlib
import re
import sqlite3

import pytest
from argon2 import extract_parameters, Type

from app import create_app
from config import load_config, validate_config
from lab.database import connect, list_users, reset_db
from lab.hashing import generate_password, hash_password, validate_password, verify_password
from export_hashes import export_lines
from keyspace_calculator import calculate
from seed_demo import seed


@pytest.fixture
def app(tmp_path, monkeypatch):
    for name in ('HOST', 'PORT', 'LAB_CAPTURE_MODE', 'LAB_LAN_MODE', 'ARGON_MEMORY_COST', 'ARGON_TIME_COST', 'ARGON_PARALLELISM'):
        monkeypatch.delenv(name, raising=False)
    return create_app({'TESTING': True, 'DATABASE': str(tmp_path / 'lab.db'), 'ARGON_MEMORY_COST': 1024, 'ARGON_TIME_COST': 1, 'ARGON_PARALLELISM': 1})


def post(client, route, data, **kwargs):
    response = client.get(route)
    token = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
    assert token, response.text
    return client.post(route, data={**data, 'csrf_token': token.group(1)}, **kwargs)


@pytest.mark.parametrize('version', ['v1', 'v2', 'v3'])
def test_exact_sha256(app, version):
    password = 'Abcde12!'
    encoded = hash_password(version, password, app.config)
    assert encoded == hashlib.sha256(password.encode()).hexdigest()
    assert encoded == hash_password(version, password, app.config)


@pytest.mark.parametrize('password', ['abcde12!', 'ABCDE12!', 'Abcde1!!', 'Abcde12 ', 'Abcde12!\n', 'Ábcde12!', 'Abcde１２!'])
def test_v3_policy_rejects(password):
    with pytest.raises(ValueError):
        validate_password('v3', password)


@pytest.mark.parametrize('version', ['v4', 'v5'])
def test_argon2_unique_salt_and_verification(app, version):
    password = 'fictional-only-20-plus!'
    encoded = hash_password(version, password, app.config)
    other = hash_password(version, password, app.config)
    assert encoded.startswith('$argon2id$')
    assert encoded != other
    assert encoded.split('$')[4] != other.split('$')[4]
    params = extract_parameters(encoded)
    assert params.type == Type.ID and params.salt_len == 16
    assert params.memory_cost == 1024 and params.time_cost == 1 and params.parallelism == 1
    assert verify_password(version, encoded, password, app.config)
    assert not verify_password(version, encoded, 'wrong', app.config)


@pytest.mark.parametrize('version,password', [('v1','123456'), ('v2','Password1!'), ('v3','Abcde12!'), ('v4','123456'), ('v5','A-long-fictional-pass!')])
def test_register_logout_login_export(app, version, password):
    client = app.test_client()
    response = post(client, '/' + version, dict(action='register', username='test_user', password=password), follow_redirects=True)
    assert 'Hola, test_user' in response.text
    rows = list_users(app.config['DATABASE'], version)
    assert len(rows) == 1
    assert 'password' not in rows[0].keys()
    assert export_lines(app.config['DATABASE'], version) == ['test_user:' + rows[0]['password_hash']]
    assert export_lines(app.config['DATABASE'], version, True) == [rows[0]['password_hash']]
    with client.session_transaction() as session:
        token = session['csrf']
    client.post('/logout/' + version, data={'csrf_token':token})
    response = post(client, '/' + version, dict(action='login', username='test_user', password='wrong'), follow_redirects=True)
    assert 'incorrectos' in response.text
    response = post(client, '/' + version, dict(action='login', username='test_user', password=password), follow_redirects=True)
    assert 'Hola, test_user' in response.text


def test_policy_applied_on_registration(app):
    client = app.test_client()
    for version in ('v3', 'v5'):
        post(client, '/' + version, dict(action='register', username='test_user', password='123456'))
    assert not list_users(app.config['DATABASE'])


def test_same_password_two_accounts_has_unique_salts(app):
    client = app.test_client()
    for version in ('v4', 'v5'):
        for user in ('user_one', 'user_two'):
            # New browser to display registration form.
            client = app.test_client()
            post(client, '/' + version, dict(action='register', username=user, password='fictional-only-20-plus!'))
        rows = list_users(app.config['DATABASE'], version)
        assert len(rows) == 2 and rows[0]['password_hash'] != rows[1]['password_hash']


def test_capture_off_by_default_and_no_plaintext(app):
    assert load_config()['LAB_CAPTURE_MODE'] is False
    client = app.test_client()
    client.get('/v1')
    with client.session_transaction() as session:
        token = session['csrf']
    response = client.post('/plot-twist', data=dict(csrf_token=token, username='fictional', password='test', fictional='yes'))
    assert response.status_code == 403
    with connect(app.config['DATABASE']) as db:
        assert db.execute('SELECT count(*) FROM captures').fetchone()[0] == 0


def test_capture_opt_in_separate_reset(app):
    app.config['LAB_CAPTURE_MODE'] = True
    client = app.test_client()
    post(client, '/plot-twist', dict(username='fictional', password='TEST-ONLY', fictional='yes'))
    with connect(app.config['DATABASE']) as db:
        assert db.execute('SELECT fictional_password FROM captures').fetchone()[0] == 'TEST-ONLY'
    assert export_lines(app.config['DATABASE'], 'v5') == []
    post(client, '/v1', dict(action='register', username='test_user', password='123456'))
    post(client, '/reset', dict(confirmation='no'))
    assert len(list_users(app.config['DATABASE'])) == 1
    post(client, '/reset', dict(confirmation='RESET'))
    assert not list_users(app.config['DATABASE'])
    with connect(app.config['DATABASE']) as db:
        assert db.execute('SELECT count(*) FROM captures').fetchone()[0] == 0


def test_cli_reset_does_not_reassign_old_session(app):
    old = app.test_client()
    post(old, '/v1', dict(action='register', username='old_user', password='123456'))
    reset_db(app.config['DATABASE'])
    new = app.test_client()
    post(new, '/v1', dict(action='register', username='new_user', password='123456'))
    assert 'Hola, new_user' not in old.get('/v1').text
    assert 'Crear cuenta ficticia' in old.get('/v1').text


@pytest.mark.parametrize('route', ['/database-viewer', '/reset', '/plot-twist'])
def test_admin_denied_from_lan_even_with_forwarded_header(app, route):
    app.config['LAB_LAN_MODE'] = True
    result = app.test_client().get(route, environ_base={'REMOTE_ADDR':'192.168.1.22'}, headers={'X-Forwarded-For':'127.0.0.1'})
    assert result.status_code == 403


def test_network_csrf_and_host_boundaries(app):
    client = app.test_client()
    assert client.get('/lab', environ_base={'REMOTE_ADDR':'192.168.1.22'}).status_code == 403
    app.config['LAB_LAN_MODE'] = True
    assert client.get('/lab', environ_base={'REMOTE_ADDR':'192.168.1.22'}).status_code == 200
    assert client.get('/lab', environ_base={'REMOTE_ADDR':'8.8.8.8'}).status_code == 403
    assert client.get('/lab', headers={'Host':'evil.example'}).status_code == 400
    assert client.post('/v1', data=dict(action='register', username='test_user', password='123456')).status_code == 400
    client.get('/v1')
    assert client.post('/v1', data=dict(csrf_token='inválido')).status_code == 400


@pytest.mark.parametrize('host,lan', [('0.0.0.0',True), ('::',True), ('8.8.8.8',True), ('192.168.1.10',False), ('localhost',False)])
def test_invalid_config(host, lan):
    config = load_config()
    config.update(HOST=host, LAB_LAN_MODE=lan)
    with pytest.raises(ValueError):
        validate_config(config)


def test_seed_atomic_and_v5_generated(app):
    config = dict(v1='123456', v2='Password1!', v3='Abcde12!', v4='123456', v5_length=20)
    values = seed(app.config['DATABASE'], app.config, config)
    assert len(values['v5']) == 20
    assert len(list_users(app.config['DATABASE'])) == 5
    with pytest.raises(ValueError):
        seed(app.config['DATABASE'], app.config, config)
    assert len(list_users(app.config['DATABASE'])) == 5


def test_keyspace():
    total, maximum, average = calculate(10, 3, 100)
    assert total == 1000 and maximum == 10 and average == 5
    assert calculate(94, 20, 1)[0] == 94**20
    for rate in ('0', '-1', 'NaN', 'Infinity'):
        with pytest.raises(ValueError):
            calculate(94, 20, rate)


def test_generator():
    first, second = generate_password(), generate_password()
    assert len(first) == 20 and first != second
    assert all(33 <= ord(c) <= 126 for c in first)


def test_templates_and_local_assets(app):
    client = app.test_client()
    for route in ('/lab', '/v1', '/v2', '/v3', '/v4', '/v5', '/database-viewer', '/reset', '/plot-twist'):
        response = client.get(route)
        assert response.status_code == 200
        assert 'ANORMALIX SECURITY LAB' in response.text
        assert 'no-store' in response.headers['Cache-Control']
    assert 'LOCAL SECURITY LAB — TEST CREDENTIALS ONLY' in client.get('/plot-twist').text
