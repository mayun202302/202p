#!/bin/bash

# TRX能量租赁系统部署脚本

# 输出彩色文本
print_green() {
    echo -e "\e[32m$1\e[0m"
}

print_yellow() {
    echo -e "\e[33m$1\e[0m"
}

print_red() {
    echo -e "\e[31m$1\e[0m"
}

print_green "===== TRX能量租赁系统部署脚本 ====="
echo ""

# 检查是否安装了Python
if ! command -v python3 &> /dev/null; then
    print_red "错误: 未找到Python3，请先安装"
    exit 1
fi

# 获取Python版本
PYTHON_VERSION=$(python3 --version)
print_yellow "检测到Python版本: $PYTHON_VERSION"

# 检查是否安装了pip
if ! command -v pip3 &> /dev/null; then
    print_red "错误: 未找到pip3，请先安装"
    exit 1
fi

# 检查.env文件
if [ ! -f ".env" ]; then
    print_yellow "未找到.env文件，从模板创建..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_green ".env文件已创建，请编辑它并填入您的配置"
    else
        print_red "错误: 未找到.env.example模板文件"
        exit 1
    fi
fi

# 创建虚拟环境
print_yellow "创建Python虚拟环境..."
python3 -m venv venv
source venv/bin/activate

# 安装依赖
print_yellow "安装依赖..."
pip install -e .

# 数据库迁移
print_yellow "初始化数据库..."
export FLASK_APP=trx_energy_rental.app
flask db init
flask db migrate -m "initial migration"
flask db upgrade

print_green "===== 部署完成 ====="
print_green "您现在可以使用以下命令启动服务:"
echo ""
print_yellow "启动Web应用:"
echo "trx-web"
echo ""
print_yellow "启动Telegram机器人:"
echo "trx-bot"
echo ""
print_yellow "启动能量监控服务:"
echo "trx-monitor"
echo ""
print_yellow "或者您可以使用supervisor来管理这些服务"
echo "配置示例在doc/supervisor目录下" 