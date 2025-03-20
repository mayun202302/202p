import os
from dotenv import load_dotenv
from pathlib import Path

# 加载.env文件
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Flask配置
SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
FLASK_APP = os.getenv('FLASK_APP', 'app.py')
FLASK_ENV = os.getenv('FLASK_ENV', 'development')

# 数据库配置
DATABASE_URL = os.getenv('DATABASE_URL')

# TRON网络配置
TRON_NETWORK = os.getenv('TRON_NETWORK', 'nile')
TRON_GRID_API = os.getenv('TRON_GRID_API')
TRON_FULL_NODE_API = os.getenv('TRON_FULL_NODE_API')

# 地址配置
OWNER_ADDRESS = os.getenv('OWNER_ADDRESS')
AGENT_ADDRESS = os.getenv('AGENT_ADDRESS')
MONITOR_ADDRESS = os.getenv('MONITOR_ADDRESS')

# 私钥配置
AGENT_PRIVATE_KEY = os.getenv('AGENT_PRIVATE_KEY')

# Telegram机器人配置
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# 能量租赁配置
RENTAL_PRICE = float(os.getenv('RENTAL_PRICE', 0.1))
RENTAL_ENERGY = int(os.getenv('RENTAL_ENERGY', 11800))
RENTAL_TIME = int(os.getenv('RENTAL_TIME', 10))
MIN_USER_ENERGY = int(os.getenv('MIN_USER_ENERGY', 60000))

# 检查必需的配置
def validate_config():
    required_configs = [
        'SECRET_KEY', 'DATABASE_URL', 'TRON_GRID_API', 'TRON_FULL_NODE_API',
        'OWNER_ADDRESS', 'AGENT_ADDRESS', 'MONITOR_ADDRESS', 'AGENT_PRIVATE_KEY',
        'TELEGRAM_BOT_TOKEN'
    ]
    
    missing_configs = []
    for config in required_configs:
        if not globals().get(config):
            missing_configs.append(config)
    
    if missing_configs:
        raise ValueError(f"缺少必要的配置项: {', '.join(missing_configs)}") 