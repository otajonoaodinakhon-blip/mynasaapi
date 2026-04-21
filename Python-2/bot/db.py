from sqlalchemy import create_engine, Column, Integer, String, BigInteger, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from contextlib import contextmanager
from bot.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class PostedItem(Base):
    __tablename__ = "posted_items"
    nasa_date = Column(String(10), primary_key=True)
    image_url = Column(String(500), nullable=False)


class BotUser(Base):
    __tablename__ = "bot_users"
    user_id = Column(BigInteger, primary_key=True)
    is_subscribed = Column(Boolean, default=False)


class RequiredChannel(Base):
    __tablename__ = "required_channels"
    channel_username = Column(String(64), primary_key=True)


class Setting(Base):
    __tablename__ = "settings"
    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


@contextmanager
def session_scope():
    s = SessionLocal()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()


def get_setting(key: str, default: str = "") -> str:
    with session_scope() as s:
        row = s.query(Setting).filter_by(key=key).first()
        return row.value if row else default


def set_setting(key: str, value: str):
    with session_scope() as s:
        row = s.query(Setting).filter_by(key=key).first()
        if row:
            row.value = value
        else:
            s.add(Setting(key=key, value=value))
