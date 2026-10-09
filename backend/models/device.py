"""
Device and Login History models for user behavior and security profiling.
"""

from datetime import datetime
from backend.extensions import db


class UserDevice(db.Model):
    __tablename__ = 'user_devices'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    device_id = db.Column(db.String(80), nullable=False)
    device_name = db.Column(db.String(120), default='Smartphone')
    ip_address = db.Column(db.String(45), default='127.0.0.1')
    location = db.Column(db.String(80), default='Hyderabad')
    is_trusted = db.Column(db.Boolean, default=True)
    last_used_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='devices')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_id': self.device_id,
            'device_name': self.device_name,
            'ip_address': self.ip_address,
            'location': self.location,
            'is_trusted': self.is_trusted,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None
        }


class LoginHistory(db.Model):
    __tablename__ = 'login_history'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    ip_address = db.Column(db.String(45), default='127.0.0.1')
    device_id = db.Column(db.String(80), default='Unknown')
    location = db.Column(db.String(80), default='Unknown')
    status = db.Column(db.String(20), default='SUCCESS')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', back_populates='login_history')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'device_id': self.device_id,
            'location': self.location,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
