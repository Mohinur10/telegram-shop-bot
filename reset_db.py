# reset_db.py – yaratilgan bazani o'chiradi va yangidan yaratadi

from models import Base, engine

if __name__ == "__main__":
    # Eski jadvallarni o'chirish
    Base.metadata.drop_all(engine)
    print("[OK] Eski jadvallar o'chirildi.")

    # Yangi jadvallar yaratish
    Base.metadata.create_all(engine)
    print("[OK] Yangi jadvallar yaratildi.")
