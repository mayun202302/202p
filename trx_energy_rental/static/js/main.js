// TRX能量租赁系统 JavaScript文件

// 复制文本到剪贴板
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        alert('文本已复制到剪贴板');
    }).catch(function(err) {
        console.error('复制失败:', err);
    });
}

// 检查支付状态
function checkPaymentStatus(tronAddress) {
    const statusElement = document.getElementById('payment-status');
    if (!statusElement) return;
    
    statusElement.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"></div> 检查支付状态...';
    
    fetch(`/api/check_payment/${tronAddress}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                statusElement.innerHTML = '<span class="badge bg-success">支付成功</span> 能量已代理';
                
                // 显示租赁详情
                const detailsElement = document.getElementById('rental-details');
                if (detailsElement) {
                    detailsElement.classList.remove('d-none');
                    document.getElementById('rental-address').textContent = data.data.rental_address;
                    document.getElementById('rental-energy').textContent = data.data.energy_amount;
                    document.getElementById('rental-time').textContent = data.data.remaining_minutes + ' 分钟';
                }
                
                // 移除检查按钮
                const checkButton = document.getElementById('check-payment-btn');
                if (checkButton) {
                    checkButton.classList.add('d-none');
                }
                
                // 启动倒计时
                startCountdown(data.data.remaining_minutes);
            } else if (data.status === 'pending') {
                statusElement.innerHTML = '<span class="badge bg-warning">处理中</span> 支付已收到，系统正在处理';
                setTimeout(() => checkPaymentStatus(tronAddress), 5000);
            } else if (data.status === 'failed') {
                statusElement.innerHTML = '<span class="badge bg-danger">失败</span> 租赁处理失败，请联系管理员';
            } else {
                statusElement.innerHTML = '<span class="badge bg-secondary">等待支付</span> 未检测到支付';
                setTimeout(() => checkPaymentStatus(tronAddress), 10000);
            }
        })
        .catch(error => {
            console.error('检查支付状态出错:', error);
            statusElement.innerHTML = '<span class="badge bg-danger">错误</span> 检查支付状态时出错';
        });
}

// 启动倒计时
function startCountdown(minutes) {
    const countdownElement = document.getElementById('countdown');
    if (!countdownElement) return;
    
    let totalSeconds = minutes * 60;
    
    const countdownInterval = setInterval(() => {
        if (totalSeconds <= 0) {
            clearInterval(countdownInterval);
            countdownElement.innerHTML = '已过期';
            countdownElement.classList.remove('text-success');
            countdownElement.classList.add('text-danger');
            return;
        }
        
        const displayMinutes = Math.floor(totalSeconds / 60);
        const displaySeconds = totalSeconds % 60;
        
        countdownElement.textContent = `${displayMinutes}:${displaySeconds < 10 ? '0' : ''}${displaySeconds}`;
        totalSeconds--;
    }, 1000);
}

// 检查能量状态
function checkEnergyStatus(tronAddress) {
    const statusElement = document.getElementById('energy-status');
    if (!statusElement) return;
    
    fetch(`/api/energy_status/${tronAddress}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                statusElement.innerHTML = `当前能量: <span class="${data.has_enough ? 'text-success' : 'text-warning'}">${data.energy}</span>`;
                
                // 显示提示信息
                const messageElement = document.getElementById('energy-message');
                if (messageElement) {
                    if (data.has_enough) {
                        messageElement.innerHTML = '<div class="alert alert-info">您已有足够能量，无需租赁</div>';
                        // 禁用租赁按钮
                        const rentButton = document.getElementById('rent-button');
                        if (rentButton) {
                            rentButton.disabled = true;
                            rentButton.classList.add('disabled');
                        }
                    } else {
                        messageElement.innerHTML = '<div class="alert alert-success">可以租赁能量</div>';
                    }
                }
            } else {
                statusElement.innerHTML = '<span class="text-danger">无法获取能量信息</span>';
            }
        })
        .catch(error => {
            console.error('检查能量状态出错:', error);
            statusElement.innerHTML = '<span class="text-danger">检查能量状态时出错</span>';
        });
}

// 当页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 为所有复制按钮添加事件监听器
    document.querySelectorAll('.copy-btn').forEach(button => {
        button.addEventListener('click', function() {
            const text = this.getAttribute('data-copy');
            copyToClipboard(text);
        });
    });
    
    // 检查支付状态
    const paymentStatusElement = document.getElementById('payment-status');
    if (paymentStatusElement) {
        const tronAddress = paymentStatusElement.getAttribute('data-address');
        if (tronAddress) {
            checkPaymentStatus(tronAddress);
        }
    }
    
    // 检查能量状态
    const energyCheckButton = document.getElementById('check-energy-btn');
    if (energyCheckButton) {
        energyCheckButton.addEventListener('click', function() {
            const addressInput = document.getElementById('tron_address');
            if (addressInput && addressInput.value) {
                checkEnergyStatus(addressInput.value);
            } else {
                alert('请输入TRON地址');
            }
        });
    }
}); 