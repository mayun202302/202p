from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
import re

class LoginForm(FlaskForm):
    """登录表单"""
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')

class RegisterForm(FlaskForm):
    """注册表单"""
    username = StringField('用户名', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    tron_address = StringField('TRON地址', validators=[DataRequired(), Length(min=34, max=34)])
    password = PasswordField('密码', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')
    
    def validate_tron_address(self, tron_address):
        """验证TRON地址格式"""
        if not re.match(r'^T[a-zA-Z0-9]{33}$', tron_address.data):
            raise ValidationError('无效的TRON地址格式')

class RentEnergyForm(FlaskForm):
    """租赁能量表单"""
    tron_address = StringField('TRON地址', validators=[DataRequired(), Length(min=34, max=34)])
    submit = SubmitField('租赁能量')
    
    def validate_tron_address(self, tron_address):
        """验证TRON地址格式"""
        if not re.match(r'^T[a-zA-Z0-9]{33}$', tron_address.data):
            raise ValidationError('无效的TRON地址格式')

class RecoverEnergyForm(FlaskForm):
    """回收能量表单"""
    tron_address = StringField('TRON地址', validators=[DataRequired(), Length(min=34, max=34)])
    submit = SubmitField('回收能量')
    
    def validate_tron_address(self, tron_address):
        """验证TRON地址格式"""
        if not re.match(r'^T[a-zA-Z0-9]{33}$', tron_address.data):
            raise ValidationError('无效的TRON地址格式') 