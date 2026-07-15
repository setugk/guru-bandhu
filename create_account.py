"""
Create or reset a guru account. Run inside the container on the NAS:

  sudo docker exec -it guru-app python create_account.py
"""
import getpass

import db

db.init_db()

username = input('Username: ').strip()
teacher_name = input('Teacher name: ').strip()
password = getpass.getpass('Password: ')
confirm = getpass.getpass('Confirm password: ')

if password != confirm:
    print('Passwords did not match.')
else:
    account_id = db.create_or_update_account(username, password, teacher_name)
    print(f'Account "{username}" ready (id={account_id}).')
