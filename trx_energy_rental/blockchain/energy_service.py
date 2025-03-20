import logging
import threading
import time
import schedule
from datetime import datetime, timedelta
from .tron_client import TronClient
from ..database.models import db, EnergyRental
from ..config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnergyRentalService:
    """能量租赁服务"""
    
    def __init__(self, db_session=None):
        self.tron_client = TronClient()
        self.db_session = db_session
        self.monitoring_tasks = {}  # 用于存储监控任务
        self.scheduler_thread = None
        self.is_running = False
    
    def start_monitoring(self):
        """启动监控服务"""
        if self.is_running:
            logger.warning("监控服务已在运行")
            return
        
        self.is_running = True
        
        # 启动监控C地址的进程
        monitor_thread = threading.Thread(target=self._monitor_payments)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 启动任务调度器
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info("能量租赁监控服务已启动")
    
    def stop_monitoring(self):
        """停止监控服务"""
        self.is_running = False
        logger.info("能量租赁监控服务已停止")
    
    def _run_scheduler(self):
        """运行调度任务"""
        # 每分钟检查一次过期的租赁
        schedule.every(1).minutes.do(self._check_expired_rentals)
        
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)
    
    def _check_expired_rentals(self):
        """检查并处理过期租赁"""
        if not self.db_session:
            logger.error("数据库会话未初始化")
            return
            
        try:
            # 查询所有状态为active但已过期的租赁
            now = datetime.utcnow()
            expired_rentals = EnergyRental.query.filter(
                EnergyRental.status == 'active',
                EnergyRental.expiry_time <= now
            ).all()
            
            for rental in expired_rentals:
                logger.info(f"处理过期租赁 ID: {rental.id}, 地址: {rental.rental_address}")
                self._recover_energy(rental)
                
        except Exception as e:
            logger.error(f"检查过期租赁失败: {str(e)}")
    
    def _monitor_payments(self):
        """监控C地址收到的付款"""
        while self.is_running:
            try:
                # 获取监听地址的交易历史
                transactions = self.tron_client.get_transactions(
                    self.tron_client.monitor_address,
                    limit=10
                )
                
                for tx in transactions:
                    # 检查是否是向监听地址转账的交易
                    if (tx.get('to') == self.tron_client.monitor_address and 
                        float(tx.get('amount', 0)) / 1e6 >= settings.RENTAL_PRICE):
                        
                        # 获取支付者地址
                        sender_address = tx.get('from')
                        tx_id = tx.get('txID')
                        
                        # 验证交易是否在近期发生（防止处理旧交易）
                        tx_time = datetime.fromtimestamp(tx.get('timestamp', 0) / 1000)
                        if datetime.now() - tx_time > timedelta(minutes=5):
                            continue
                            
                        # 检查是否已处理过该交易
                        if self._is_transaction_processed(tx_id):
                            continue
                        
                        # 处理新付款
                        self._process_new_payment(sender_address, tx_id)
                
                # 每3秒检查一次
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"监控付款时出错: {str(e)}")
                time.sleep(5)  # 出错后等待较长时间
    
    def _is_transaction_processed(self, tx_id):
        """检查交易是否已被处理"""
        if not self.db_session:
            return False
            
        try:
            rental = EnergyRental.query.filter_by(payment_txid=tx_id).first()
            return rental is not None
        except Exception as e:
            logger.error(f"检查交易处理状态时出错: {str(e)}")
            return False
    
    def _process_new_payment(self, sender_address, tx_id):
        """处理新支付，为用户代理能量"""
        try:
            logger.info(f"收到来自 {sender_address} 的新支付，交易ID: {tx_id}")
            
            # 检查用户是否已有足够能量
            if self.tron_client.check_enough_energy(sender_address):
                logger.info(f"用户 {sender_address} 已有足够能量，不提供租赁服务")
                return
                
            # 创建租赁记录
            rental = self._create_rental_record(sender_address, tx_id)
            
            # 代理能量给用户
            success = self._delegate_energy(rental)
            
            if success:
                # 启动监控用户TRC20转账的任务
                self._start_monitoring_user_tx(rental)
        except Exception as e:
            logger.error(f"处理新支付时出错: {str(e)}")
    
    def _create_rental_record(self, address, tx_id):
        """创建租赁记录"""
        if not self.db_session:
            logger.error("数据库会话未初始化")
            return None
            
        try:
            # 计算到期时间
            expiry_time = datetime.utcnow() + timedelta(minutes=settings.RENTAL_TIME)
            
            # 创建新的租赁记录
            rental = EnergyRental(
                rental_address=address,
                energy_amount=settings.RENTAL_ENERGY,
                payment_txid=tx_id,
                status='pending',
                expiry_time=expiry_time
            )
            
            # 保存到数据库
            db.session.add(rental)
            db.session.commit()
            
            logger.info(f"已创建租赁记录，ID: {rental.id}, 地址: {address}")
            return rental
            
        except Exception as e:
            logger.error(f"创建租赁记录时出错: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            return None
    
    def _delegate_energy(self, rental):
        """代理能量给用户"""
        if not rental:
            return False
            
        try:
            # 代理能量
            txid = self.tron_client.delegate_resource(
                rental.rental_address,
                rental.energy_amount
            )
            
            if txid:
                # 更新租赁记录
                rental.delegate_txid = txid
                rental.status = 'active'
                db.session.commit()
                
                logger.info(f"成功代理能量，租赁ID: {rental.id}, 交易ID: {txid}")
                return True
            else:
                # 代理失败
                rental.status = 'failed'
                db.session.commit()
                
                logger.error(f"代理能量失败，租赁ID: {rental.id}")
                return False
                
        except Exception as e:
            logger.error(f"代理能量时出错: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            return False
    
    def _start_monitoring_user_tx(self, rental):
        """开始监控用户交易，若用户进行了TRC20转账，则回收能量"""
        if not rental or rental.status != 'active':
            return
            
        # 创建监控任务
        task = threading.Thread(
            target=self._monitor_user_transactions,
            args=(rental,)
        )
        task.daemon = True
        task.start()
        
        # 记录任务
        self.monitoring_tasks[rental.id] = task
        
        logger.info(f"已开始监控用户 {rental.rental_address} 的交易")
    
    def _monitor_user_transactions(self, rental):
        """监控用户交易"""
        # 记录开始监控的时间
        start_time = datetime.utcnow()
        
        # 设置过期时间
        timeout_time = start_time + timedelta(minutes=settings.RENTAL_TIME)
        
        while datetime.utcnow() < timeout_time and rental.status == 'active':
            try:
                # 检查用户是否进行了TRC20转账
                tx_id = self.tron_client.check_trc20_transfer(rental.rental_address, start_time)
                
                if tx_id:
                    logger.info(f"检测到用户 {rental.rental_address} 进行了TRC20转账，交易ID: {tx_id}")
                    
                    # 更新租赁记录
                    rental.actual_usage_txid = tx_id
                    db.session.commit()
                    
                    # 回收能量
                    self._recover_energy(rental)
                    break
                    
                # 每3秒检查一次
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"监控用户交易时出错: {str(e)}")
                time.sleep(5)
        
        # 如果监控结束但未触发回收，则检查是否需要回收能量
        if rental.status == 'active':
            logger.info(f"用户 {rental.rental_address} 的能量租赁已到期，回收能量")
            self._recover_energy(rental)
    
    def _recover_energy(self, rental):
        """回收代理给用户的能量"""
        if not rental or rental.status != 'active':
            return
            
        try:
            # 回收能量
            txid = self.tron_client.undelegate_resource(rental.rental_address)
            
            if txid:
                # 更新租赁记录
                rental.recover_txid = txid
                rental.status = 'completed'
                db.session.commit()
                
                logger.info(f"成功回收能量，租赁ID: {rental.id}, 交易ID: {txid}")
                
                # 移除监控任务
                if rental.id in self.monitoring_tasks:
                    del self.monitoring_tasks[rental.id]
            else:
                logger.error(f"回收能量失败，租赁ID: {rental.id}")
                
        except Exception as e:
            logger.error(f"回收能量时出错: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
    
    def manual_delegate(self, address, energy_amount=None):
        """手动为地址代理能量"""
        if energy_amount is None:
            energy_amount = settings.RENTAL_ENERGY
            
        try:
            # 检查用户是否已有足够能量
            if self.tron_client.check_enough_energy(address):
                logger.info(f"用户 {address} 已有足够能量，不提供租赁服务")
                return False, "用户已有足够能量"
                
            # 创建租赁记录（手动模式，无支付交易ID）
            rental = EnergyRental(
                rental_address=address,
                energy_amount=energy_amount,
                payment_txid="manual_operation",
                status='pending',
                expiry_time=datetime.utcnow() + timedelta(minutes=settings.RENTAL_TIME)
            )
            
            db.session.add(rental)
            db.session.commit()
            
            # 代理能量
            success = self._delegate_energy(rental)
            
            if success:
                # 启动监控
                self._start_monitoring_user_tx(rental)
                return True, f"成功为 {address} 代理 {energy_amount} 能量"
            else:
                return False, "代理能量失败"
                
        except Exception as e:
            logger.error(f"手动代理能量失败: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            return False, f"发生错误: {str(e)}"
    
    def manual_recover(self, address):
        """手动回收代理给地址的能量"""
        try:
            # 查找该地址的活跃租赁
            rental = EnergyRental.query.filter_by(
                rental_address=address,
                status='active'
            ).first()
            
            if not rental:
                return False, f"未找到地址 {address} 的活跃租赁"
                
            # 回收能量
            self._recover_energy(rental)
            return True, f"已回收代理给 {address} 的能量"
            
        except Exception as e:
            logger.error(f"手动回收能量失败: {str(e)}")
            return False, f"发生错误: {str(e)}"

def monitor_main():
    """命令行入口点，启动能量监控服务"""
    # 验证配置
    from ..config import validate_config
    
    try:
        validate_config()
    except ValueError as e:
        print(f"配置错误: {str(e)}")
        import sys
        sys.exit(1)
    
    # 创建Flask应用上下文以获取数据库会话
    from ..app import create_app
    from ..database.models import db
    
    app = create_app()
    
    print("启动能量监控服务...")
    
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

if __name__ == "__main__":
    monitor_main() 