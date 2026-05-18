# 连锁餐饮 AI 系统

基于 FastAPI + LangChain + AI 的连锁餐饮智能管理系统。

## 项目结构

```
├── app/                        # 应用主代码
├── Base/                       # 基础模块
├── doc/
│   └── sql/
│       ├── schema.sql          # 数据库表结构 DDL
│       ├── generate_data.py    # 模拟数据生成脚本
│       └── README.md           # 数据生成使用说明
├── requirements.txt
└── README.md
```

## 模拟数据生成

数据生成脚本位于 `doc/sql/` 目录，用于生成门店营业模拟数据。

### 生成的数据范围

- **门店**: 500 家，均匀分布全国 31 个省级行政区
- **菜品**: 56 道中式快餐常见菜品
- **订单**: 堂食 + 外卖订单，含订单明细
- **营业汇总**: 每日每店聚合数据
- **评论**: 模拟美团、饿了么、大众点评等平台评论
- **用户**: 总部管理员 + 员工 + 加盟商账号

### 生成策略

- **按天循环**: 从 2023-01-01 开始逐天生成，而非逐店生成
- **门店随机选取**: 每天随机选取 85%~95% 的营业门店
- **每月提交**: 月份切换时提交数据库，大幅减少 I/O
- **价格统一**: 同一门店的同一种菜品价格始终一致
- **高峰时段**: 下单时间集中在午餐（11:00-13:00）和晚餐（17:00-19:00）

### 使用方法

```bash
cd doc/sql
python generate_data.py
```

可通过环境变量配置数据库连接：
```bash
DB_HOST=localhost DB_PORT=3306 DB_USER=root DB_PASSWORD=xxx python generate_data.py
```

详细说明见 `doc/sql/README.md`。

## 常用命令

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
pip freeze > requirements.txt
```
