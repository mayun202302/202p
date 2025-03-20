import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler
from ..blockchain.energy_service import EnergyRentalService
from ..blockchain.tron_client import TronClient
from ..database.models import EnergyRental, User, db
from ..config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramBot:
    """TG机器人"""
    
    def __init__(self, db_session=None):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.db_session = db_session
        self.energy_service = EnergyRentalService(db_session)
        self.tron_client = TronClient()
        
        # 检查Token是否设置
        if not self.token:
            logger.error("Telegram机器人Token未设置")
            raise ValueError("缺少Telegram机器人Token")
    
    def start(self):
        """启动机器人"""
        # 创建Updater并传入Token
        updater = Updater(self.token)
        
        # 获取调度程序注册处理程序
        dp = updater.dispatcher
        
        # 注册命令处理程序
        dp.add_handler(CommandHandler("start", self.start_command))
        dp.add_handler(CommandHandler("help", self.help_command))
        dp.add_handler(CommandHandler("rent", self.rent_command))
        dp.add_handler(CommandHandler("status", self.status_command))
        dp.add_handler(CommandHandler("address", self.address_command))
        dp.add_handler(CommandHandler("recover", self.recover_command))
        
        # 注册消息处理程序
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.handle_message))
        
        # 注册回调查询处理程序
        dp.add_handler(CallbackQueryHandler(self.button_callback))
        
        # 注册错误处理程序
        dp.add_error_handler(self.error_handler)
        
        # 启动机器人
        updater.start_polling()
        logger.info("Telegram机器人已启动")
        
        # 启动能量服务监控
        self.energy_service.start_monitoring()
        
        # 运行机器人，直到按下Ctrl+C或进程收到停止信号
        updater.idle()
        
        # 停止能量服务监控
        self.energy_service.stop_monitoring()
    
    def start_command(self, update: Update, context: CallbackContext):
        """处理/start命令"""
        user = update.effective_user
        
        welcome_message = (
            f"你好 {user.first_name}！欢迎使用TRX能量租赁机器人。\n\n"
            "本机器人可以帮助你租赁TRON网络能量，以便进行低成本交易。\n\n"
            "使用 /help 命令查看帮助信息。"
        )
        
        update.message.reply_text(welcome_message)
    
    def help_command(self, update: Update, context: CallbackContext):
        """处理/help命令"""
        help_message = (
            "TRX能量租赁机器人帮助：\n\n"
            "/start - 开始使用机器人\n"
            "/help - 显示帮助信息\n"
            "/rent <TRON地址> - 为指定地址租赁能量\n"
            "/status - 查询当前租赁状态\n"
            "/address - 显示支付地址\n"
            "/recover <TRON地址> - 手动回收租赁给指定地址的能量\n\n"
            f"租赁价格：{settings.RENTAL_PRICE} TRX\n"
            f"租赁能量：{settings.RENTAL_ENERGY}\n"
            f"租赁时间：{settings.RENTAL_TIME} 分钟\n\n"
            "注意：\n"
            "1. 如果您已有超过60,000能量，则无法租赁\n"
            "2. 一旦使用能量进行TRC20转账，系统将立即回收剩余能量\n"
            "3. 租赁将在10分钟后自动过期"
        )
        
        update.message.reply_text(help_message)
    
    def rent_command(self, update: Update, context: CallbackContext):
        """处理/rent命令"""
        if not context.args or len(context.args) != 1:
            update.message.reply_text("请提供TRON地址，例如：/rent TXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXxx")
            return
        
        tron_address = context.args[0]
        
        # 验证TRON地址格式
        if not self._is_valid_tron_address(tron_address):
            update.message.reply_text("请提供有效的TRON地址")
            return
        
        # 检查用户是否已有足够能量
        if self.tron_client.check_enough_energy(tron_address):
            update.message.reply_text(f"地址 {tron_address} 已有足够能量，不需要租赁")
            return
        
        # 给用户显示付款信息
        payment_info = (
            f"要为地址 {tron_address} 租赁能量，请发送 {settings.RENTAL_PRICE} TRX 到以下地址：\n\n"
            f"`{self.tron_client.monitor_address}`\n\n"
            "支付成功后，系统将自动为您代理能量。\n"
            "请注意：\n"
            "1. 租赁时长为10分钟\n"
            "2. 如果您在此期间进行TRC20转账，系统将立即回收剩余能量\n"
            "3. 请确保从您要租赁能量的地址发起支付"
        )
        
        keyboard = [
            [InlineKeyboardButton("检查支付状态", callback_data=f"check_payment:{tron_address}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(payment_info, parse_mode='Markdown', reply_markup=reply_markup)
    
    def status_command(self, update: Update, context: CallbackContext):
        """处理/status命令"""
        user_id = update.effective_user.id
        
        # 查询用户绑定的TRON地址
        user = User.query.filter_by(telegram_id=str(user_id)).first()
        
        if not user or not user.tron_address:
            update.message.reply_text("您尚未绑定TRON地址，请使用 /rent <TRON地址> 命令租赁能量")
            return
        
        # 查询该地址的活跃租赁
        rental = EnergyRental.query.filter_by(
            rental_address=user.tron_address,
            status='active'
        ).first()
        
        if rental:
            # 计算剩余时间
            remaining_minutes = rental.remaining_time
            
            status_message = (
                f"您当前有一个活跃的能量租赁：\n\n"
                f"TRON地址：{rental.rental_address}\n"
                f"租赁能量：{rental.energy_amount}\n"
                f"剩余时间：{remaining_minutes} 分钟\n"
                f"能量使用情况：{'已使用' if rental.actual_usage_txid else '未使用'}\n\n"
                "提示：完成TRC20转账后，系统将自动回收剩余能量"
            )
        else:
            # 查询该地址的历史租赁
            completed_rentals = EnergyRental.query.filter_by(
                rental_address=user.tron_address,
                status='completed'
            ).order_by(EnergyRental.updated_at.desc()).limit(3).all()
            
            if completed_rentals:
                status_message = "您近期的能量租赁记录：\n\n"
                for i, rental in enumerate(completed_rentals, 1):
                    status_message += (
                        f"{i}. 租赁时间：{rental.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"   能量：{rental.energy_amount}\n"
                        f"   状态：已完成\n\n"
                    )
                
                status_message += "当前没有活跃的能量租赁，使用 /rent 命令租赁新能量"
            else:
                status_message = "您当前没有活跃的能量租赁，也没有历史租赁记录"
        
        update.message.reply_text(status_message)
    
    def address_command(self, update: Update, context: CallbackContext):
        """处理/address命令，显示支付地址"""
        payment_address = (
            f"能量租赁支付地址：\n\n"
            f"`{self.tron_client.monitor_address}`\n\n"
            f"租赁价格：{settings.RENTAL_PRICE} TRX\n"
            f"租赁能量：{settings.RENTAL_ENERGY}\n"
            f"租赁时间：{settings.RENTAL_TIME} 分钟"
        )
        
        update.message.reply_text(payment_address, parse_mode='Markdown')
    
    def recover_command(self, update: Update, context: CallbackContext):
        """处理/recover命令，手动回收租赁给指定地址的能量"""
        if not context.args or len(context.args) != 1:
            update.message.reply_text("请提供TRON地址，例如：/recover TXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXxx")
            return
        
        tron_address = context.args[0]
        
        # 验证TRON地址格式
        if not self._is_valid_tron_address(tron_address):
            update.message.reply_text("请提供有效的TRON地址")
            return
        
        # 手动回收能量
        success, message = self.energy_service.manual_recover(tron_address)
        
        update.message.reply_text(message)
    
    def handle_message(self, update: Update, context: CallbackContext):
        """处理用户发送的普通消息"""
        user_text = update.message.text
        
        # 检查是否是TRON地址
        if self._is_valid_tron_address(user_text):
            # 用户直接发送了TRON地址，视为租赁请求
            context.args = [user_text]
            self.rent_command(update, context)
            return
        
        # 其他消息
        update.message.reply_text(
            "如需租赁能量，请使用 /rent <TRON地址> 命令\n"
            "如需帮助，请使用 /help 命令"
        )
    
    def button_callback(self, update: Update, context: CallbackContext):
        """处理内联键盘按钮回调"""
        query = update.callback_query
        query.answer()
        
        # 获取回调数据
        callback_data = query.data
        
        if callback_data.startswith("check_payment:"):
            # 检查支付状态
            tron_address = callback_data.split(":")[1]
            
            # 查询该地址的活跃租赁
            rental = EnergyRental.query.filter_by(
                rental_address=tron_address,
                status='active'
            ).first()
            
            if rental:
                query.edit_message_text(
                    f"您的支付已确认，能量已成功租赁给地址 {tron_address}\n"
                    f"租赁能量：{rental.energy_amount}\n"
                    f"租赁时间：{settings.RENTAL_TIME} 分钟\n\n"
                    "注意：\n"
                    "1. 如果您在此期间进行TRC20转账，系统将立即回收剩余能量\n"
                    "2. 租赁将在10分钟后自动过期"
                )
            else:
                # 查询该地址的待处理租赁
                pending_rental = EnergyRental.query.filter_by(
                    rental_address=tron_address,
                    status='pending'
                ).first()
                
                if pending_rental:
                    query.edit_message_text(
                        "您的支付已收到，系统正在处理中...\n"
                        "请稍后再次检查状态"
                    )
                else:
                    # 查询是否有失败的租赁
                    failed_rental = EnergyRental.query.filter_by(
                        rental_address=tron_address,
                        status='failed'
                    ).order_by(EnergyRental.updated_at.desc()).first()
                    
                    if failed_rental:
                        query.edit_message_text(
                            "租赁处理失败，请联系管理员解决\n"
                            "或使用 /rent 命令重新尝试"
                        )
                    else:
                        # 未检测到支付或租赁记录
                        keyboard = [
                            [InlineKeyboardButton("再次检查", callback_data=f"check_payment:{tron_address}")]
                        ]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        msg_text = (
                            f"尚未检测到您的支付\n"
                            f"请向地址 {self.tron_client.monitor_address} 支付 {settings.RENTAL_PRICE} TRX\n"
                            f"支付完成后点击\"再次检查\"按钮"
                        )
                        query.edit_message_text(text=msg_text, reply_markup=reply_markup)
    
    def error_handler(self, update: Update, context: CallbackContext):
        """处理错误"""
        logger.error(f"更新 {update} 导致错误 {context.error}")
    
    def _is_valid_tron_address(self, address):
        """验证TRON地址格式"""
        # TRON地址通常以T开头，后跟33个字符
        return bool(re.match(r'^T[a-zA-Z0-9]{33}$', address))
    
    def _associate_telegram_user(self, telegram_id, tron_address):
        """关联Telegram用户与TRON地址"""
        try:
            # 查找现有用户
            user = User.query.filter_by(telegram_id=str(telegram_id)).first()
            
            if user:
                # 更新地址
                user.tron_address = tron_address
            else:
                # 创建新用户
                user = User(
                    username=f"tg_user_{telegram_id}",
                    email=f"tg_user_{telegram_id}@example.com",  # 占位
                    tron_address=tron_address,
                    telegram_id=str(telegram_id)
                )
                db.session.add(user)
            
            db.session.commit()
            return True
        except Exception as e:
            logger.error(f"关联Telegram用户与TRON地址失败: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            return False

def main():
    """命令行入口点，启动Telegram机器人"""
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
    
    # 在应用上下文中运行机器人
    with app.app_context():
        bot = TelegramBot(db.session)
        bot.start()

if __name__ == "__main__":
    main() 