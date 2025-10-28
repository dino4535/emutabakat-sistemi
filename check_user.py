#!/usr/bin/env python
# -*- coding: utf-8 -*-

from backend.database import SessionLocal
from backend.models import User
import sys

username = sys.argv[1] if len(sys.argv) > 1 else "58825193742"

db = SessionLocal()
user = db.query(User).filter(User.username == username).first()

if user:
    print(f"\n[OK] Kullanici bulundu: {username}")
    print(f"  - ID: {user.id}")
    print(f"  - Username: {user.username}")
    print(f"  - Email: {user.email or '[YOK]'}")
    print(f"  - Role: {user.role}")
    print(f"  - Active: {user.is_active}")
    print(f"  - Verified: {user.is_verified}")
    print(f"  - Password hash: {'[VAR]' if user.hashed_password else '[YOK]'}")
    print(f"  - VKN/TCKN: {user.vkn_tckn or '[YOK]'}")
    print(f"  - Ilk giris: {user.ilk_giris_tamamlandi}")
else:
    print(f"\n[X] Kullanici bulunamadi: {username}")

db.close()

