"""One-time security bootstrap for the isolated localhost development instance."""
import secrets
from pathlib import Path
import pymysql
root=Path(__file__).resolve().parents[1]
if (root/'.env').exists():
    raise SystemExit('Existing connection configuration preserved')
c=pymysql.connect(host='127.0.0.1',port=3307,user='root')
password=secrets.token_urlsafe(32)
c.cursor().execute("ALTER USER 'root'@'localhost' IDENTIFIED BY %s",(password,))
(root/'.env').write_text('MYSQL_URL=mysql+pymysql://root:'+password+'@127.0.0.1:3307/motorsport_aero\n')
c.close()
print('Isolated local database secured. Connection stored in ignored .env.')
