import os
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate

from .database.models import db, User
from .app.routes import main, auth, api
from .blockchain.energy_service import EnergyRentalService
from .config import settings, validate_config

def create_app(test_config=None):
    """创建并配置Flask应用"""
    # 创建应用实例
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')
    
    # 加载配置
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 如果是测试配置
    if test_config:
        app.config.update(test_config)
    
    # 确保实例文件夹存在
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # 初始化数据库
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # 初始化登录管理器
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'info'
    login_manager.init_app(app)
    
    # 用户加载回调
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # 注册蓝图
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(api, url_prefix='/api')
    
    # 创建数据库表（如果不存在）
    with app.app_context():
        db.create_all()
    
    return app

def run_bot():
    """运行Telegram机器人"""
    from .bot.telegram_bot import TelegramBot
    
    # 验证配置
    validate_config()
    
    # 创建应用以获取数据库会话
    app = create_app()
    
    # 在应用上下文中运行机器人
    with app.app_context():
        bot = TelegramBot(db.session)
        bot.start()

def run_energy_service():
    """运行能量监控服务（不含Web应用和机器人）"""
    # 验证配置
    validate_config()
    
    # 创建应用以获取数据库会话
    app = create_app()
    
    # 在应用上下文中运行能量服务
    with app.app_context():
        service = EnergyRentalService(db.session)
        service.start_monitoring()
        
        # 保持服务运行
        import time
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            service.stop_monitoring()
            print("能量监控服务已停止")

def main():
    """命令行入口点，启动Web应用"""
    try:
        validate_config()
    except ValueError as e:
        print(f"配置错误: {str(e)}")
        import sys
        sys.exit(1)
    
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    import sys
    
    # 验证配置
    try:
        validate_config()
    except ValueError as e:
        print(f"配置错误: {str(e)}")
        sys.exit(1)
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == 'bot':
            print("启动Telegram机器人...")
            run_bot()
        elif sys.argv[1] == 'service':
            print("启动能量监控服务...")
            run_energy_service()
        else:
            print("未知的命令行参数，使用方法：")
            print("python -m trx_energy_rental.app                 # 启动Web应用")
            print("python -m trx_energy_rental.app bot             # 启动Telegram机器人")
            print("python -m trx_energy_rental.app service         # 启动能量监控服务")
    else:
        # 默认启动Web应用
        main() 