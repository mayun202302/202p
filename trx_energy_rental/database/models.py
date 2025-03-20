from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    tron_address = db.Column(db.String(34), unique=True, nullable=False)
    telegram_id = db.Column(db.String(20), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 一对多关系
    rentals = db.relationship('EnergyRental', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'


class EnergyRental(db.Model):
    """能量租赁记录模型"""
    __tablename__ = 'energy_rentals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    rental_address = db.Column(db.String(34), nullable=False)  # 租赁者的波场地址
    energy_amount = db.Column(db.BigInteger, nullable=False)  # 租赁的能量数量
    payment_txid = db.Column(db.String(64), nullable=False)  # 支付的交易ID
    delegate_txid = db.Column(db.String(64), nullable=True)  # 代理能量的交易ID
    recover_txid = db.Column(db.String(64), nullable=True)  # 回收能量的交易ID
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, active, completed, failed
    expiry_time = db.Column(db.DateTime, nullable=False)  # 到期时间
    actual_usage_txid = db.Column(db.String(64), nullable=True)  # 实际使用能量的交易ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EnergyRental {self.id} - {self.rental_address}>'
    
    @property
    def is_expired(self):
        """检查租赁是否已过期"""
        return datetime.utcnow() > self.expiry_time
    
    @property
    def remaining_time(self):
        """获取剩余租赁时间（分钟）"""
        if self.is_expired:
            return 0
        
        delta = self.expiry_time - datetime.utcnow()
        return max(0, int(delta.total_seconds() / 60))


class SystemStatus(db.Model):
    """系统状态模型"""
    __tablename__ = 'system_status'
    
    id = db.Column(db.Integer, primary_key=True)
    total_energy_available = db.Column(db.BigInteger, nullable=False, default=0)
    total_energy_used = db.Column(db.BigInteger, nullable=False, default=0)
    active_rentals = db.Column(db.Integer, nullable=False, default=0)
    total_revenue = db.Column(db.Float, nullable=False, default=0)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemStatus {self.id}>' 