import time
import logging
from tronpy import Tron
from tronpy.keys import PrivateKey
from tronpy.exceptions import TransactionError
from datetime import datetime, timedelta
from ..config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TronClient:
    """TRON区块链客户端"""
    
    def __init__(self):
        # 初始化TRON客户端，根据配置选择主网或测试网
        if settings.TRON_NETWORK.lower() == 'mainnet':
            self.client = Tron()
        else:
            self.client = Tron(network='nile')
        
        # 设置地址
        self.owner_address = settings.OWNER_ADDRESS  # A地址
        self.agent_address = settings.AGENT_ADDRESS  # B地址
        self.monitor_address = settings.MONITOR_ADDRESS  # C地址
        
        # 加载B地址私钥
        if settings.AGENT_PRIVATE_KEY:
            self.agent_priv_key = PrivateKey(bytes.fromhex(settings.AGENT_PRIVATE_KEY))
        else:
            self.agent_priv_key = None
            logger.warning("代理地址私钥未配置，无法进行签名操作")
    
    def get_account_info(self, address):
        """获取账户信息"""
        try:
            account = self.client.get_account(address)
            return account
        except Exception as e:
            logger.error(f"获取账户 {address} 信息失败: {str(e)}")
            return None
    
    def get_account_resource(self, address):
        """获取账户资源信息"""
        try:
            account_resource = self.client.get_account_resource(address)
            return account_resource
        except Exception as e:
            logger.error(f"获取账户 {address} 资源信息失败: {str(e)}")
            return None
    
    def get_account_energy(self, address):
        """获取账户可用能量"""
        try:
            account_resource = self.client.get_account_resource(address)
            
            # 获取能量信息
            energy_limit = account_resource.get('energy_limit', 0)
            energy_used = account_resource.get('energy_used', 0)
            
            # 计算可用能量
            available_energy = max(0, energy_limit - energy_used)
            return available_energy
        except Exception as e:
            logger.error(f"获取账户 {address} 能量信息失败: {str(e)}")
            return 0
    
    def check_enough_energy(self, address, required_energy=settings.MIN_USER_ENERGY):
        """检查账户是否有足够的能量"""
        available_energy = self.get_account_energy(address)
        return available_energy >= required_energy
    
    def delegate_resource(self, receiver_address, energy_amount=settings.RENTAL_ENERGY):
        """代理资源给接收者地址"""
        if not self.agent_priv_key:
            logger.error("代理地址私钥未配置，无法进行签名操作")
            return None
            
        try:
            # 使用B地址签名，使A地址代理资源给D地址
            txn = (
                self.client.trx.freeze_balance(
                    self.owner_address,  # A地址
                    energy_amount,  # 能量数量
                    "ENERGY",  # 资源类型
                    receiver_address  # D地址
                )
                .with_owner(self.agent_address)  # B地址作为交易发起者
                .build()
                .sign(self.agent_priv_key)
            )
            
            # 广播交易
            result = txn.broadcast()
            
            # 检查交易结果
            if result.get("result", False):
                logger.info(f"成功代理 {energy_amount} 能量给 {receiver_address}")
                return result.get("txid")
            else:
                logger.error(f"代理能量失败: {result}")
                return None
                
        except TransactionError as e:
            logger.error(f"代理能量交易错误: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"代理能量异常: {str(e)}")
            return None
    
    def undelegate_resource(self, receiver_address):
        """收回代理给接收者的资源"""
        if not self.agent_priv_key:
            logger.error("代理地址私钥未配置，无法进行签名操作")
            return None
            
        try:
            # 使用B地址签名，收回A地址代理给D地址的资源
            txn = (
                self.client.trx.unfreeze_balance(
                    self.owner_address,  # A地址
                    "ENERGY",  # 资源类型
                    receiver_address  # D地址
                )
                .with_owner(self.agent_address)  # B地址作为交易发起者
                .build()
                .sign(self.agent_priv_key)
            )
            
            # 广播交易
            result = txn.broadcast()
            
            # 检查交易结果
            if result.get("result", False):
                logger.info(f"成功回收代理给 {receiver_address} 的能量")
                return result.get("txid")
            else:
                logger.error(f"回收代理能量失败: {result}")
                return None
                
        except TransactionError as e:
            logger.error(f"回收代理能量交易错误: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"回收代理能量异常: {str(e)}")
            return None
    
    def get_transactions(self, address, only_trc20=False, limit=10):
        """获取地址的交易历史"""
        try:
            # 调用TRON API获取交易历史
            transactions = self.client.get_account_transactions(address, limit=limit)
            
            # 如果只需要TRC20交易
            if only_trc20:
                trc20_txs = []
                for tx in transactions:
                    # 检查是否为TRC20交易
                    if 'contract_address' in tx and tx.get('type') == 'TransferContract':
                        trc20_txs.append(tx)
                return trc20_txs
            
            return transactions
        except Exception as e:
            logger.error(f"获取地址 {address} 交易历史失败: {str(e)}")
            return []
    
    def check_trc20_transfer(self, address, start_time):
        """检查地址在起始时间后是否有TRC20转账交易"""
        try:
            transactions = self.get_transactions(address, only_trc20=True, limit=20)
            
            for tx in transactions:
                # 获取交易时间
                tx_time = datetime.fromtimestamp(tx.get('timestamp', 0) / 1000)
                
                # 判断交易是否在起始时间之后
                if tx_time > start_time:
                    return tx.get('txID')  # 返回交易ID
            
            return None  # 没有找到符合条件的交易
        except Exception as e:
            logger.error(f"检查地址 {address} TRC20转账交易失败: {str(e)}")
            return None
    
    def check_payment(self, sender_address, amount=settings.RENTAL_PRICE, timeout=60):
        """检查发送者是否向监听地址支付了指定金额"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=timeout)
        
        while datetime.now() < end_time:
            try:
                # 获取监听地址收到的交易
                transactions = self.client.get_account_transactions(self.monitor_address, limit=10)
                
                for tx in transactions:
                    # 检查是否是从sender_address转账到monitor_address的交易
                    if (tx.get('from') == sender_address and 
                        tx.get('to') == self.monitor_address and 
                        float(tx.get('amount', 0)) / 1e6 >= amount):
                        
                        # 获取交易时间
                        tx_time = datetime.fromtimestamp(tx.get('timestamp', 0) / 1000)
                        
                        # 检查交易是否在查询开始之后发生
                        if tx_time > start_time - timedelta(minutes=2):  # 允许2分钟的时间误差
                            return tx.get('txID')  # 返回交易ID
                
                # 休眠一段时间再查询
                time.sleep(3)
            except Exception as e:
                logger.error(f"检查支付失败: {str(e)}")
                time.sleep(3)
        
        return None  # 超时未检测到支付 