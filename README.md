# TRX能量租赁系统

TRON区块链能量租赁服务，包含Web应用和Telegram机器人。

## 项目简介

TRX能量租赁系统是一个完整的TRON能量租赁服务，旨在帮助用户以低成本获取TRON网络上的能量资源。系统采用代理能量模式，用户无需提供私钥即可租赁能量。

## 主要特点

- **Web应用程序**: 提供直观的网页界面进行能量租赁操作
- **Telegram机器人**: 支持通过Telegram进行快速能量租赁
- **交易监控**: 自动监控交易并处理能量租赁请求
- **安全代理授权**: 基于TRON网络的能量代理授权模式，无需用户提供私钥

## 技术架构

- **后端**: Python + Flask
- **数据库**: MySQL/MariaDB
- **区块链交互**: tronpy, tron-api-python
- **Telegram机器人**: python-telegram-bot

## 项目结构

```
trx_energy_rental/
├── app/            - Web应用相关模块
├── blockchain/     - 区块链交互模块
├── bot/            - Telegram机器人模块
├── config/         - 配置管理模块
├── database/       - 数据库模型与操作
├── static/         - 静态资源文件
├── templates/      - HTML模板文件
└── utils/          - 公共工具函数
```

## 安装与使用

请参考 [详细文档](trx_energy_rental/README.md) 了解完整的安装和使用说明。

## 命令行工具

安装后，可以使用以下命令运行不同组件：

```bash
# 启动Web应用
trx-web

# 启动Telegram机器人
trx-bot

# 启动能量监控服务
trx-monitor
```

## 作者

TRX Energy Rental Team

## 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件 