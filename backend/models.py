from datetime import date, datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from database import Base


# Django admin equivalents (for reference):
# User -> auth.User or custom User model
# FoodLog, ScanLog, Recommendation, Reminder, FoodPrice -> app models


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    age = Column(Integer)
    weight_kg = Column(Float)
    height_cm = Column(Float)
    gender = Column(String(10))
    goal = Column(String(20))
    daily_calorie_goal = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    food_logs = relationship("FoodLog", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")


class FoodLog(Base):
    __tablename__ = "food_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    food_name = Column(String(200), nullable=False)
    quantity_g = Column(Float)
    calories = Column(Float)
    protein_g = Column(Float)
    carbs_g = Column(Float)
    fat_g = Column(Float)
    meal_type = Column(String(20))
    scan_time = Column(DateTime, default=datetime.utcnow)
    ai_confidence = Column(Float, nullable=True)
    calorie_range_min = Column(Float, nullable=True)
    calorie_range_max = Column(Float, nullable=True)

    user = relationship("User", back_populates="food_logs")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="recommendations")


class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    scan_date = Column(Date, default=date.today)
    scan_count = Column(Integer, default=1)

    __table_args__ = (UniqueConstraint("user_id", "scan_date", name="uq_user_scan_date"),)


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    type = Column(String(30), nullable=False)  # meal, water, protein_alert
    scheduled_at = Column(DateTime, nullable=False)
    payload = Column(Text, nullable=True)  # JSON context
    sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class FoodPrice(Base):
    __tablename__ = "food_prices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    region = Column(String(50), default="kerala")
    price_low = Column(Integer, nullable=True)  # rupees
    price_high = Column(Integer, nullable=True)  # rupees


class WeightLog(Base):
    __tablename__ = "weight_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    weight_kg = Column(Float, nullable=False)
    logged_at = Column(DateTime, default=datetime.utcnow)


class ReminderSchedule(Base):
    __tablename__ = "reminder_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    type = Column(String(30), nullable=False)  # breakfast, lunch, dinner, water, goal_alert
    enabled = Column(Boolean, default=True, nullable=False)
    scheduled_time = Column(String(8), nullable=True)  # "HH:MM" in 24h format
    timezone = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    type = Column(String(50), nullable=True)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    payload = Column(Text, nullable=True)  # JSON payload
    sent_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    endpoint = Column(Text, nullable=False, unique=True)
    p256dh = Column(String(255), nullable=False)
    auth = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    is_super = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
