from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer, String, DateTime, func


class Base(DeclarativeBase):
    pass

class RainConditions(Base):
    __tablename__ = "RainConditions"
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id = mapped_column(String(50), nullable=False)
    device_id = mapped_column(String(50), nullable=False)
    rain_location_longitude = mapped_column(Integer, nullable=False)
    rain_location_latitude = mapped_column(Integer, nullable=False)
    rainfall_nm = mapped_column(Integer, nullable=False)
    intensity = mapped_column(String(50), nullable=False)
    timestamp = mapped_column(DateTime, nullable=False)
    date_created = mapped_column(DateTime, nullable=False, default=func.now())

    def to_dict(self):
            return {
                "trace_id": self.trace_id,
                "device_id": self.device_id,
                "rain_location_longitude": self.rain_location_longitude,
                "rain_location_latitude": self.rain_location_latitude,
                "rainfall_nm": self.rainfall_nm,
                "intensity": self.intensity,
                "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            }

class Floodings(Base):
    __tablename__ = "floodings"
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id = mapped_column(String(50), nullable=False)
    device_id = mapped_column(String(50), nullable=False)
    flood_location_longitude = mapped_column(Integer, nullable=False)
    flood_location_latitude = mapped_column(Integer, nullable=False)
    flood_level = mapped_column(Integer, nullable=False)
    severity = mapped_column(String(50), nullable=False)
    timestamp = mapped_column(DateTime, nullable=False)
    date_created = mapped_column(DateTime, nullable=False, default=func.now())
    
    def to_dict(self):
        return {
            "trace_id": self.trace_id,
            "device_id": self.device_id,
            "flood_location_longitude": self.flood_location_longitude,
            "flood_location_latitude": self.flood_location_latitude,
            "flood_level": self.flood_level,
            "severity": self.severity,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }
