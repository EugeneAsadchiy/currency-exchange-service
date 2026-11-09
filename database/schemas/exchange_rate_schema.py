from sqlalchemy import Column, Integer, String, Date, Numeric, UniqueConstraint

from database.schemas.base import Base


class ExchangeRateSchema(Base):
    __tablename__ = "exchange_rates"
    __table_args__ = (UniqueConstraint("rate_date", "currency_code", name="uq_exchange_rates_date_currency"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    rate_date = Column(Date, nullable=False)
    currency_code = Column(String(3), nullable=False)
    scale = Column(Integer, nullable=False)
    official_rate = Column(Numeric(18, 6), nullable=False)
