# TRX能量租赁系统部署指南

本文档提供了TRX能量租赁系统的详细部署指南，包括环境准备、安装步骤、配置说明和服务管理。

## 环境要求

- Python 3.8+
- MySQL 5.7+ / MariaDB 10.5+
- Supervisor (推荐用于生产环境)
- Nginx (可选，用于生产环境Web服务)

## 安装步骤

### 1. 准备环境

首先，确保系统已安装Python 3.8+和MySQL/MariaDB：

```bash
# Debian/Ubuntu
sudo apt update
sudo apt install python3 python3-pip python3-venv mysql-server supervisor nginx

# CentOS/RHEL
sudo yum install python3 python3-pip mysql-server supervisor nginx
```

### 2. 克隆代码

```bash
git clone https://github.com/yourusername/trx_energy_rental.git
cd trx_energy_rental
```

### 3. 配置环境

创建并编辑环境变量文件：

```bash
cp .env.example .env
# 使用编辑器修改.env文件
nano .env
```

主要配置项说明：

- **SECRET_KEY**: Flask应用密钥，建议生成随机字符串
- **DATABASE_URL**: 数据库连接字符串
- **TRON_NETWORK**: TRON网络类型，mainnet或nile
- **OWNER_ADDRESS**: A地址，拥有能量的地址
- **AGENT_ADDRESS**: B地址，代理签名的地址
- **MONITOR_ADDRESS**: C地址，监听支付的地址
- **AGENT_PRIVATE_KEY**: B地址的私钥
- **TELEGRAM_BOT_TOKEN**: Telegram机器人的Token

### 4. 创建数据库

```bash
mysql -u root -p
```

在MySQL提示符下执行：

```sql
CREATE DATABASE trx_energy_rental CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'trx_user'@'localhost' IDENTIFIED BY 'your_strong_password';
GRANT ALL PRIVILEGES ON trx_energy_rental.* TO 'trx_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

更新.env文件中的数据库连接字符串：

```
DATABASE_URL="mysql+pymysql://trx_user:your_strong_password@localhost/trx_energy_rental"
```

### 5. 使用部署脚本安装

我们提供了一个自动化部署脚本，可以简化安装过程：

```bash
chmod +x deploy.sh
./deploy.sh
```

或者手动执行以下步骤：

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -e .

# 初始化数据库
export FLASK_APP=trx_energy_rental.app
flask db init
flask db migrate -m "initial migration"
flask db upgrade
```

## 运行服务

### 开发环境

在开发环境中，您可以直接运行命令启动各项服务：

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动Web应用
trx-web

# 启动Telegram机器人
trx-bot

# 启动能量监控服务
trx-monitor
```

### 生产环境

对于生产环境，我们推荐使用Supervisor管理服务：

1. 复制Supervisor配置模板：

```bash
sudo cp doc/supervisor/trx_energy_rental.conf /etc/supervisor/conf.d/
```

2. 编辑配置文件，修改路径和用户名：

```bash
sudo nano /etc/supervisor/conf.d/trx_energy_rental.conf
```

3. 创建日志目录：

```bash
sudo mkdir -p /var/log/trx_energy_rental
sudo chown -R your_username:your_group /var/log/trx_energy_rental
```

4. 重新加载Supervisor配置：

```bash
sudo supervisorctl reread
sudo supervisorctl update
```

5. 检查服务状态：

```bash
sudo supervisorctl status trx_energy_rental:*
```

### 使用Nginx部署Web应用

1. 创建Nginx配置文件：

```bash
sudo nano /etc/nginx/sites-available/trx_energy_rental
```

2. 添加以下配置：

```nginx
server {
    listen 80;
    server_name your_domain.com;

    access_log /var/log/nginx/trx_energy_rental.access.log;
    error_log /var/log/nginx/trx_energy_rental.error.log;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

3. 启用站点并重启Nginx：

```bash
sudo ln -s /etc/nginx/sites-available/trx_energy_rental /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## 升级和更新

要更新系统，请按照以下步骤操作：

```bash
# 进入项目目录
cd /path/to/trx_energy_rental

# 拉取最新代码
git pull

# 激活虚拟环境
source venv/bin/activate

# 更新依赖
pip install -e .

# 升级数据库
export FLASK_APP=trx_energy_rental.app
flask db migrate -m "update migration"
flask db upgrade

# 重启服务
sudo supervisorctl restart trx_energy_rental:*
```

## 日常维护

### 查看日志

```bash
# 查看Web应用日志
sudo tail -f /var/log/trx_energy_rental/web.log

# 查看Telegram机器人日志
sudo tail -f /var/log/trx_energy_rental/bot.log

# 查看能量监控服务日志
sudo tail -f /var/log/trx_energy_rental/monitor.log
```

### 备份数据库

建议定期备份数据库：

```bash
# 创建备份
mysqldump -u trx_user -p trx_energy_rental > backup_$(date +%Y%m%d).sql

# 恢复备份
mysql -u trx_user -p trx_energy_rental < backup_20230101.sql
```

## 故障排除

### 服务无法启动

检查日志文件了解详细错误：

```bash
sudo tail -f /var/log/trx_energy_rental/*.log
```

常见问题：
- 配置文件.env不存在或配置错误
- 数据库连接失败
- TRON节点API不可用

### 能量租赁失败

可能的原因：
- A地址能量不足
- B地址私钥错误
- TRON网络拥堵导致交易延迟

### 监控服务问题

如果监控服务不正常工作：
- 检查C地址是否正确
- 确认服务正在运行：`sudo supervisorctl status trx_energy_rental:trx-monitor`
- 查看日志：`sudo tail -f /var/log/trx_energy_rental/monitor.log`

## 安全考虑

- 定期更新服务器系统
- 使用防火墙限制访问
- 保护私钥和.env文件
- 定期更改数据库密码
- 使用HTTPS协议保护Web应用 