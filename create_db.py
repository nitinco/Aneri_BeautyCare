import os
import urllib.parse as urlparse
import pymysql

# Read DATABASE_URL or use XAMPP defaults
DATABASE_URL = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:@localhost:3306/aneri_beauty_care')

# parse format mysql+pymysql://user:pass@host:port/dbname
if DATABASE_URL.startswith('mysql'):
    # strip the driver prefix
    rest = DATABASE_URL.split('://', 1)[1]
    # use urlparse to split
    parsed = urlparse.urlparse('//' + rest)
    user = parsed.username or 'root'
    password = parsed.password or ''
    host = parsed.hostname or 'localhost'
    port = parsed.port or 3306
    dbname = parsed.path.lstrip('/') or 'aneri_beauty_care'

    print(f"Creating database '{dbname}' on {host}:{port} as user '{user}' (if not exists)")
    try:
        conn = pymysql.connect(host=host, user=user, password=password, port=port)
        conn.autocommit(True)
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{dbname}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print('Database ensured.')
        cur.close()
        conn.close()
    except Exception as e:
        print('Failed to create database:', e)
        raise
else:
    print('DATABASE_URL does not look like MySQL. Please set DATABASE_URL to a mysql+pymysql URL.')
    raise SystemExit(1)
