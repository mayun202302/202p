import re
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_valid_tron_address(address):
    """验证TRON地址格式"""
    # TRON地址通常以T开头，后跟33个字符
    return bool(re.match(r'^T[a-zA-Z0-9]{33}$', address))

def format_transaction_id(tx_id, max_length=10):
    """格式化交易ID，截断过长的部分"""
    if not tx_id:
        return "无"
    if len(tx_id) > max_length * 2:
        return f"{tx_id[:max_length]}...{tx_id[-max_length:]}"
    return tx_id

def format_datetime(dt):
    """格式化日期时间为易读格式"""
    if not dt:
        return "无"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def trx_to_sun(trx_amount):
    """将TRX转换为SUN (1 TRX = 1,000,000 SUN)"""
    return int(float(trx_amount) * 1_000_000)

def sun_to_trx(sun_amount):
    """将SUN转换为TRX (1 TRX = 1,000,000 SUN)"""
    return float(sun_amount) / 1_000_000

def get_readable_time_from_seconds(seconds):
    """将秒数转换为易读的时间格式"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}分{remaining_seconds}秒"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}小时{minutes}分" 