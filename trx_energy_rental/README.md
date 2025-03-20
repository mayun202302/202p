# TRX能量租赁系统

一个完整的TRON能量租赁系统，包括Web应用和Telegram机器人。

## 功能特点

- **网页端能量租赁**：通过网页端进行TRON能量租赁
- **Telegram机器人**：支持通过Telegram机器人进行能量租赁
- **代理模式**：采用代理授权模式，无需用户私钥，安全可靠
- **智能监控**：自动监控用户交易，完成后立即回收能量
- **超时回收**：租赁时间到期后自动回收能量
- **能量检测**：检测用户当前能量，已有足够能量的用户不提供租赁服务

## 系统需求

- Python 3.8+
- MySQL 5.7+ / MariaDB 10.5+
- TRON节点接入权限 (可使用公共API)

## 安装方法

1. 克隆代码库:

```bash
git clone https://github.com/yourusername/trx_energy_rental.git
cd trx_energy_rental
```

2. 安装所需依赖:

```bash
pip install -r requirements.txt
```

3. 复制配置模板并修改:

```bash
cp config/.env.example config/.env
```

4. 编辑 `config/.env` 文件，填入必要参数:
   - 设置数据库连接字符串
   - 设置TRON网络相关参数
   - 设置A地址（能量拥有者）、B地址（代理签名者）和C地址（监听地址）
   - 设置B地址的私钥
   - 设置Telegram机器人Token

## 配置说明

### 地址配置

系统使用三个关键地址:

- **A地址 (OWNER_ADDRESS)**: 质押了TRX并拥有能量的地址
- **B地址 (AGENT_ADDRESS)**: 有权代理A地址资源的签名地址，需要提供其私钥
- **C地址 (MONITOR_ADDRESS)**: 用于接收用户支付的监听地址

### 能量代理配置

- **RENTAL_PRICE**: 租赁价格 (单位: TRX)
- **RENTAL_ENERGY**: 租赁能量数量
- **RENTAL_TIME**: 租赁时长 (单位: 分钟)
- **MIN_USER_ENERGY**: 最低能量阈值，超过此值的用户不提供租赁服务

## 启动方法

系统支持三种启动方式:

### 1. 启动Web应用

```bash
python -m trx_energy_rental.app
```

Web应用默认运行在 http://localhost:5000

### 2. 启动Telegram机器人

```bash
python -m trx_energy_rental.app bot
```

### 3. 启动能量监控服务

```bash
python -m trx_energy_rental.app service
```

在生产环境中，建议使用 gunicorn 或 uwsgi 运行Web应用，使用 supervisor 或 systemd 管理Telegram机器人和能量监控服务。

## 使用流程

1. 用户访问网站或Telegram机器人
2. 输入需要租赁能量的TRON地址
3. 向指定地址支付租赁费用(0.1 TRX)
4. 系统检测到支付后，自动代理能量给用户
5. 用户使用能量进行交易，系统检测到交易后立即回收能量
6. 如果超过租赁时间(默认10分钟)未使用，系统也会自动回收能量

## 安全注意事项

- 妥善保管B地址私钥
- 定期检查代理记录，确保系统正常运行
- 确保A地址有足够的质押量和能量

## 开发者

如需贡献代码或报告问题，请提交Issue或Pull Request。

## 许可证

本项目采用MIT许可证。详情请查看LICENSE文件。 