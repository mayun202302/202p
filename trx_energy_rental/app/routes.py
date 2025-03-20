from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

from ..database.models import db, User, EnergyRental, SystemStatus
from ..blockchain.energy_service import EnergyRentalService
from ..blockchain.tron_client import TronClient
from .forms import LoginForm, RegisterForm, RentEnergyForm, RecoverEnergyForm
from ..config import settings

# 创建蓝图
main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__)
api = Blueprint('api', __name__)

# 初始化服务
tron_client = TronClient()
energy_service = EnergyRentalService()

# 主页路由
@main.route('/')
def index():
    """主页"""
    # 获取系统状态
    system_status = SystemStatus.query.first()
    if not system_status:
        system_status = SystemStatus(
            total_energy_available=0,
            total_energy_used=0,
            active_rentals=0,
            total_revenue=0,
            is_active=True
        )
        db.session.add(system_status)
        db.session.commit()
    
    # 获取最近的租赁记录
    recent_rentals = EnergyRental.query.order_by(
        EnergyRental.created_at.desc()
    ).limit(5).all()
    
    # 显示租赁表单
    rent_form = RentEnergyForm()
    
    return render_template(
        'index.html',
        system_status=system_status,
        recent_rentals=recent_rentals,
        rent_form=rent_form,
        monitor_address=tron_client.monitor_address,
        rental_price=settings.RENTAL_PRICE,
        rental_energy=settings.RENTAL_ENERGY,
        rental_time=settings.RENTAL_TIME
    )

@main.route('/rent', methods=['POST'])
def rent_energy():
    """租赁能量"""
    form = RentEnergyForm()
    
    if form.validate_on_submit():
        tron_address = form.tron_address.data
        
        # 检查地址是否有足够能量
        if tron_client.check_enough_energy(tron_address):
            flash(f'地址 {tron_address} 已有足够能量，不需要租赁', 'info')
            return redirect(url_for('main.index'))
        
        # 返回支付信息
        return render_template(
            'payment.html',
            tron_address=tron_address,
            monitor_address=tron_client.monitor_address,
            rental_price=settings.RENTAL_PRICE,
            rental_energy=settings.RENTAL_ENERGY,
            rental_time=settings.RENTAL_TIME
        )
    
    # 表单验证失败
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text}: {error}", 'danger')
    
    return redirect(url_for('main.index'))

@main.route('/rentals')
@login_required
def rentals():
    """查看用户的租赁记录"""
    # 查询用户所有租赁记录
    user_rentals = EnergyRental.query.filter_by(user_id=current_user.id)\
        .order_by(EnergyRental.created_at.desc()).all()
    
    return render_template('rentals.html', rentals=user_rentals)

@main.route('/recover', methods=['GET', 'POST'])
@login_required
def recover_energy():
    """回收能量页面"""
    form = RecoverEnergyForm()
    
    if form.validate_on_submit():
        tron_address = form.tron_address.data
        
        # 手动回收能量
        success, message = energy_service.manual_recover(tron_address)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')
        
        return redirect(url_for('main.rentals'))
    
    return render_template('recover.html', form=form)

# 认证路由
@auth.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        else:
            flash('登录失败，请检查邮箱和密码', 'danger')
    
    return render_template('login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegisterForm()
    
    if form.validate_on_submit():
        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=form.username.data).first():
            flash('用户名已被使用', 'danger')
            return render_template('register.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('邮箱已被注册', 'danger')
            return render_template('register.html', form=form)
        
        # 创建新用户
        user = User(
            username=form.username.data,
            email=form.email.data,
            tron_address=form.tron_address.data,
            password_hash=generate_password_hash(form.password.data)
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('注册成功，请登录', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    """退出登录"""
    logout_user()
    flash('已成功退出登录', 'info')
    return redirect(url_for('main.index'))

# API路由
@api.route('/check_payment/<tron_address>', methods=['GET'])
def check_payment(tron_address):
    """检查支付状态的API"""
    # 查询该地址的活跃租赁
    rental = EnergyRental.query.filter_by(
        rental_address=tron_address,
        status='active'
    ).first()
    
    if rental:
        return jsonify({
            'status': 'success',
            'message': '能量租赁已激活',
            'data': {
                'rental_id': rental.id,
                'rental_address': rental.rental_address,
                'energy_amount': rental.energy_amount,
                'expiry_time': rental.expiry_time.isoformat(),
                'remaining_minutes': rental.remaining_time
            }
        })
    
    # 查询该地址的待处理租赁
    pending_rental = EnergyRental.query.filter_by(
        rental_address=tron_address,
        status='pending'
    ).first()
    
    if pending_rental:
        return jsonify({
            'status': 'pending',
            'message': '支付已收到，正在处理中',
            'data': None
        })
    
    # 查询是否有失败的租赁
    failed_rental = EnergyRental.query.filter_by(
        rental_address=tron_address,
        status='failed'
    ).order_by(EnergyRental.updated_at.desc()).first()
    
    if failed_rental:
        return jsonify({
            'status': 'failed',
            'message': '租赁处理失败',
            'data': None
        })
    
    # 未检测到支付或租赁记录
    return jsonify({
        'status': 'not_found',
        'message': '未检测到支付',
        'data': None
    })

@api.route('/energy_status/<tron_address>', methods=['GET'])
def energy_status(tron_address):
    """获取地址能量状态"""
    try:
        energy = tron_client.get_account_energy(tron_address)
        
        return jsonify({
            'status': 'success',
            'energy': energy,
            'has_enough': energy >= settings.MIN_USER_ENERGY
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 