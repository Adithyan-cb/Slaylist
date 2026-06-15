import time
import logging
from typing import Any, Optional

from sqlalchemy import Column, Float, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.sql import select
from langchain_community.cache import SQLAlchemyCache
from langchain_core.caches import RETURN_VAL_TYPE
from langchain_core.load import dumps, loads
from langchain_core.outputs import Generation

logger = logging.getLogger(__name__)

Base = declarative_base()


class TTLCacheEntry(Base):
    __tablename__ = "llm_cache_ttl"
    prompt = Column(String, primary_key=True)
    llm = Column(String, primary_key=True)
    idx = Column(Integer, primary_key=True)
    response = Column(String)
    created_at = Column(Float, nullable=False)


class TTLSQLAlchemyCache(SQLAlchemyCache):
    def __init__(self, engine, ttl_seconds: int = 86400, cache_schema=TTLCacheEntry):
        self.ttl_seconds = ttl_seconds
        super().__init__(engine, cache_schema)

    def _clean_expired(self, session):
        cutoff = time.time() - self.ttl_seconds
        session.query(self.cache_schema).filter(
            self.cache_schema.created_at < cutoff
        ).delete()
        session.commit()

    def lookup(self, prompt: str, llm_string: str) -> Optional[RETURN_VAL_TYPE]:
        with Session(self.engine) as session:
            self._clean_expired(session)
            stmt = (
                select(self.cache_schema.response)
                .where(self.cache_schema.prompt == prompt)
                .where(self.cache_schema.llm == llm_string)
                .order_by(self.cache_schema.idx)
            )
            rows = session.execute(stmt).fetchall()
            if rows:
                try:
                    return [loads(row[0]) for row in rows]
                except Exception:
                    logger.warning("Failed to deserialize cache entry")
                    return [Generation(text=row[0]) for row in rows]
        return None

    def update(self, prompt: str, llm_string: str, return_val: RETURN_VAL_TYPE) -> None:
        items = [
            self.cache_schema(
                prompt=prompt,
                llm=llm_string,
                response=dumps(gen),
                idx=i,
                created_at=time.time(),
            )
            for i, gen in enumerate(return_val)
        ]
        with Session(self.engine) as session, session.begin():
            for item in items:
                session.merge(item)

    def clear(self, **kwargs: Any) -> None:
        with Session(self.engine) as session:
            session.query(self.cache_schema).delete()
            session.commit()
