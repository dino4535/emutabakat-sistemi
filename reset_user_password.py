import os
import sys
import bcrypt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.database import SessionLocal
from backend.models import User

def reset_user_password(vkn: str, new_password: str = None):
    """
    Kullanıcının şifresini sıfırla
    
    Args:
        vkn: Kullanıcının VKN'si
        new_password: Yeni şifre (None ise VKN'nin son 6 hanesi kullanılır)
    """
    try:
        db = SessionLocal()
        
        # Kullanıcıyı bul
        user = db.query(User).filter(User.vkn_tckn == vkn).first()
        
        if not user:
            print(f"HATA: VKN {vkn} ile eslesen kullanici bulunamadi.")
            return
        
        # Şifre belirleme
        if new_password is None:
            new_password = vkn[-6:]  # VKN'nin son 6 hanesi
        
        # Şifreyi hashle
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Kullanıcının şifresini güncelle
        user.hashed_password = hashed_password
        db.commit()
        
        print("="*80)
        print("SIFRE BASARIYLA SIFIRLANDI!")
        print("="*80)
        print(f"Kullanici ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"VKN: {user.vkn_tckn}")
        print(f"Full Name: {user.full_name}")
        print(f"Email: {user.email}")
        print(f"Yeni Sifre: {new_password}")
        print("="*80)
        print("\nKullanici artik su bilgilerle giris yapabilir:")
        print(f"  Kullanici Adi: {user.username}")
        print(f"  Sifre: {new_password}")
        print("="*80)
        
        db.close()
        
    except Exception as e:
        print(f"HATA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # VKN 0010600612 olan kullanıcının şifresini sıfırla
    vkn = "0010600612"
    reset_user_password(vkn)
