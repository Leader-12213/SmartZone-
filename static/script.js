// Tab switching for auth forms
function showTab(tabName) {
    // Hide all forms
    document.querySelectorAll('.auth-form').forEach(form => {
        form.classList.remove('active');
    });

    // Hide all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected form
    document.getElementById(tabName + '-form').classList.add('active');

    // Activate clicked tab
    event.target.classList.add('active');
}

// Currency switching for deposit
function showCurrency(currency) {
    // Hide all deposit forms
    document.querySelectorAll('.deposit-form').forEach(form => {
        form.classList.remove('active');
    });

    // Hide all currency tabs
    document.querySelectorAll('.currency-tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected form
    document.getElementById(currency + '-deposit').classList.add('active');

    // Activate clicked tab
    event.target.classList.add('active');
}

// Currency switching for withdrawal
function showWithdrawCurrency(currency) {
    // Hide all withdraw forms
    document.querySelectorAll('.withdraw-form').forEach(form => {
        form.classList.remove('active');
    });

    // Hide all currency tabs
    document.querySelectorAll('.currency-tab').forEach(tab => {
        tab.classList.remove('active');
    });

    // Show selected form
    document.getElementById(currency + '-withdraw').classList.add('active');

    // Activate clicked tab
    event.target.classList.add('active');
}

// Toast Notification System
function createToast(type, title, message, duration = 4000) {
    // Create toast container if it doesn't exist
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    // Choose icon based on type
    let icon = '';
    switch(type) {
        case 'success':
            icon = 'fas fa-check-circle';
            break;
        case 'error':
            icon = 'fas fa-exclamation-circle';
            break;
        case 'info':
            icon = 'fas fa-info-circle';
            break;
        case 'warning':
            icon = 'fas fa-exclamation-triangle';
            break;
        default:
            icon = 'fas fa-bell';
    }

    toast.innerHTML = `
        <div class="toast-icon">
            <i class="${icon}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="removeToast(this.parentElement)">
            <i class="fas fa-times"></i>
        </button>
        <div class="toast-progress"></div>
    `;

    container.appendChild(toast);

    // Auto remove after duration
    setTimeout(() => {
        removeToast(toast);
    }, duration);

    return toast;
}

function removeToast(toast) {
    if (toast && toast.parentElement) {
        toast.classList.add('removing');
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
        }, 300);
    }
}

// Copy invite code function
function copyInviteCode(inviteCode) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(inviteCode).then(function() {
            // Show success toast
            createToast('success', 'تم النسخ بنجاح!', `تم نسخ رمز الدعوة: ${inviteCode}`);

            // Change button text temporarily
            const copyBtn = event.target.closest('.copy-btn');
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = '<i class="fas fa-check"></i> تم النسخ';
            copyBtn.style.background = '#22c55e';

            // Reset button after 2 seconds
            setTimeout(function() {
                copyBtn.innerHTML = originalText;
                copyBtn.style.background = '#4ade80';
            }, 2000);
        }).catch(function(err) {
            console.error('فشل في نسخ الرمز: ', err);
            fallbackCopyTextToClipboard(inviteCode);
        });
    } else {
        fallbackCopyTextToClipboard(inviteCode);
    }
}

// Fallback copy function for older browsers
function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    textArea.style.top = "-999999px";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        document.execCommand('copy');
        // Show success toast
        createToast('success', 'تم النسخ بنجاح!', `تم نسخ رمز الدعوة: ${text}`);

        const copyBtn = event.target.closest('.copy-btn');
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fas fa-check"></i> تم النسخ';
        copyBtn.style.background = '#22c55e';

        setTimeout(function() {
            copyBtn.innerHTML = originalText;
            copyBtn.style.background = '#4ade80';
        }, 2000);
    } catch (err) {
        createToast('info', 'رمز الدعوة', `الرمز: ${text}`);
    }

    document.body.removeChild(textArea);
}

// Product purchase
function buyProduct(productType) {
    // Show confirmation toast first
    createToast('info', 'جاري المعالجة...', 'يتم الآن معالجة طلب الشراء');

    // Small delay for better UX
    setTimeout(() => {
        fetch('/buy_product', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product: productType
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                createToast('success', 'تم الشراء بنجاح!', data.message);
                // إعادة تحميل الصفحة لتحديث الرصيد
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                createToast('error', 'فشل في الشراء', data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            createToast('error', 'خطأ في الشبكة', 'حدث خطأ أثناء الشراء، يرجى المحاولة مرة أخرى');
        });
    }, 500);
}

// تحديث الأرباح اليومية
function checkProfits() {
    fetch('/check_profits')
    .then(() => {
        window.location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function joinVip1Draw() {
    if (confirm('هل تريد الانضمام للسحب على VIP1 مقابل 10 EGP؟')) {
        fetch('/join_vip1_draw', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                createToast('success', 'تم الانضمام بنجاح!', data.message);
                setTimeout(() => {
                    location.reload();
                }, 2000);
            } else {
                createToast('error', 'خطأ', data.message);
            }
        })
        .catch(error => {
            createToast('error', 'خطأ', 'حدث خطأ في الاتصال');
        });
    }
}

// Open Telegram links
function openTelegram(url) {
    window.open(url, '_blank');
}

// Auto-hide flash messages
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 300);
        }, 5000);
    });

    // Set active nav item
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
        if (item.getAttribute('href') === currentPath) {
            item.classList.add('active');
        }
    });
});

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('input[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.style.borderColor = '#e74c3c';
            isValid = false;
        } else {
            input.style.borderColor = '#e0e0e0';
        }
    });

    return isValid;
}

// Copy to clipboard function
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        alert('تم نسخ العنوان');
    });
}

// Add click event to address box
document.addEventListener('DOMContentLoaded', function() {
    const addressBox = document.querySelector('.address-box');
    if (addressBox) {
        addressBox.style.cursor = 'pointer';
        addressBox.addEventListener('click', function() {
            copyToClipboard(this.textContent);
        });
    }
});
