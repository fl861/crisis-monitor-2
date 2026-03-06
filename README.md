# 锦成盛危机监测系统 - 部署说明

## 功能特性

✅ **自动更新数据** - 每30分钟自动获取最新市场数据
✅ **实时报警** - 触发阈值时自动发送飞书通知
✅ **可视化网页** - GitHub Pages在线展示
✅ **公开数据源** - 无需付费API

---

## 快速部署

### 1. 获取 FRED API Key（免费）

1. 访问: https://fred.stlouisfed.org/docs/api/api_key.html
2. 注册账号
3. 创建免费API Key

### 2. 配置飞书 Webhook（报警通知）

1. 在飞书群组中添加"自定义机器人"
2. 获取Webhook URL

### 3. 设置定时监控

```bash
# 编辑crontab
crontab -e

# 添加以下行（每30分钟检查一次）
*/30 * * * * export FRED_API_KEY="你的API_KEY" && export FEISHU_WEBHOOK="你的Webhook" && /home/admin/.openclaw/workspace/crisis_monitor/check.sh >> /var/log/crisis_monitor.log 2>&1
```

---

## 手动运行

```bash
# 单次检查
export FRED_API_KEY="你的API_KEY"
export FEISHU_WEBHOOK="你的Webhook"
./check.sh

# 持续监控（每5分钟）
python3 monitor_daemon.py --daemon --interval 300
```

---

## 报警阈值

| 指标 | 正常 | 警戒 | 危险 | 紧急 |
|------|------|------|------|------|
| Swap Spread 3Y | >-20bp | -20~-30bp | -30~-40bp | <-40bp |
| VIX | <15 | 15-20 | 20-30 | >30 |

---

## 数据来源

| 数据 | 来源 | 更新频率 |
|------|------|----------|
| Swap Spread | FRED | 每日 |
| VIX | Yahoo Finance | 实时 |

---

## 使用模型

alibaba-cloud/glm-5