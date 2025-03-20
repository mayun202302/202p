#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TRX能量租赁系统项目检查工具

用于检查项目结构、必要文件是否存在、配置是否完整等。
"""

import os
import sys
import importlib
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 定义颜色输出
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message):
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")

def print_success(message):
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_warning(message):
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_info(message):
    print(f"{Colors.OKBLUE}ℹ {message}{Colors.ENDC}")

def check_file_exists(file_path, required=True):
    """检查文件是否存在"""
    path = project_root / file_path
    if path.exists():
        print_success(f"文件 {file_path} 存在")
        return True
    else:
        if required:
            print_error(f"必需的文件 {file_path} 不存在")
        else:
            print_warning(f"推荐的文件 {file_path} 不存在")
        return False

def check_module_importable(module_name):
    """检查模块是否可导入"""
    try:
        importlib.import_module(module_name)
        print_success(f"模块 {module_name} 可以成功导入")
        return True
    except ImportError as e:
        print_error(f"模块 {module_name} 导入失败: {str(e)}")
        return False

def check_command_available(command):
    """检查命令是否可用"""
    try:
        subprocess.run(command, capture_output=True, check=True)
        print_success(f"命令 '{' '.join(command)}' 可用")
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print_error(f"命令 '{' '.join(command)}' 不可用")
        return False

def check_env_file():
    """检查.env文件配置"""
    env_path = project_root / '.env'
    env_example_path = project_root / '.env.example'
    
    if not env_path.exists():
        if env_example_path.exists():
            print_warning("未找到.env文件，但.env.example存在。请复制并配置.env文件")
        else:
            print_error("未找到.env和.env.example文件")
        return False
    
    print_success(".env文件存在")
    
    # 读取.env文件内容
    with open(env_path, 'r', encoding='utf-8') as f:
        env_content = f.read()
    
    required_configs = [
        'SECRET_KEY', 'DATABASE_URL', 'OWNER_ADDRESS', 
        'AGENT_ADDRESS', 'MONITOR_ADDRESS', 'AGENT_PRIVATE_KEY'
    ]
    
    missing_configs = []
    for config in required_configs:
        if f"{config}=" not in env_content and f"{config} =" not in env_content:
            missing_configs.append(config)
    
    if missing_configs:
        print_error(f"缺少必要的环境变量: {', '.join(missing_configs)}")
        return False
    else:
        print_success("所有必要的环境变量都已配置")
        return True

def check_database_connection():
    """检查数据库连接"""
    try:
        # 导入项目配置模块
        from trx_energy_rental.config import settings
        
        # 导入数据库模型
        from trx_energy_rental.database.models import db
        
        # 导入Flask应用
        from trx_energy_rental.app import create_app
        
        # 创建应用
        app = create_app()
        
        # 测试数据库连接
        with app.app_context():
            db.engine.connect()
            print_success("数据库连接成功")
            return True
    except ImportError as e:
        print_error(f"导入模块失败: {str(e)}")
        return False
    except Exception as e:
        print_error(f"数据库连接失败: {str(e)}")
        return False

def main():
    """主函数"""
    print_header("TRX能量租赁系统项目检查")
    print("-" * 50)
    
    # 检查核心项目文件
    print_header("\n检查核心文件:")
    files_to_check = [
        'setup.py',
        'requirements.txt',
        'README.md',
        'LICENSE',
        '.env.example',
        'MANIFEST.in',
    ]
    
    for file in files_to_check:
        check_file_exists(file)
    
    # 检查项目结构
    print_header("\n检查项目结构:")
    directories = [
        'trx_energy_rental',
        'trx_energy_rental/app',
        'trx_energy_rental/blockchain',
        'trx_energy_rental/bot',
        'trx_energy_rental/config',
        'trx_energy_rental/database',
        'trx_energy_rental/static',
        'trx_energy_rental/templates',
        'trx_energy_rental/utils',
    ]
    
    for directory in directories:
        if os.path.isdir(project_root / directory):
            print_success(f"目录 {directory} 存在")
        else:
            print_error(f"目录 {directory} 不存在")
    
    # 检查环境变量
    print_header("\n检查环境变量:")
    check_env_file()
    
    # 检查Python模块
    print_header("\n检查Python模块:")
    modules_to_check = [
        'trx_energy_rental',
        'trx_energy_rental.app',
        'trx_energy_rental.blockchain',
        'trx_energy_rental.bot',
        'trx_energy_rental.config',
        'trx_energy_rental.database',
        'trx_energy_rental.utils',
    ]
    
    for module in modules_to_check:
        check_module_importable(module)
    
    # 检查安装的Python依赖
    print_header("\n检查Python依赖:")
    dependencies = [
        'flask',
        'flask_sqlalchemy',
        'flask_wtf',
        'flask_login',
        'tronpy',
        'python-telegram-bot',
        'python-dotenv',
    ]
    
    for dependency in dependencies:
        try:
            importlib.import_module(dependency.replace('-', '_'))
            print_success(f"依赖 {dependency} 已安装")
        except ImportError:
            print_warning(f"依赖 {dependency} 未安装或无法导入")
    
    # 检查数据库连接
    print_header("\n检查数据库连接:")
    try:
        check_database_connection()
    except Exception as e:
        print_error(f"检查数据库连接时出错: {str(e)}")
    
    print("\n" + "-" * 50)
    print_info("项目检查完成")

if __name__ == "__main__":
    main() 