#!/usr/bin/env python3
"""
连锁餐饮 AI 系统 - 模拟数据生成与插入脚本

生成数据范围：
  - 门店: 500 家，均匀分布全国各省市
  - 菜品: 31 道中式快餐常见菜品
  - 会员: 每店 30~80 名会员
  - 堂食订单: 区分会员订单与非会员订单，含支付方式
  - 外卖订单: 记录外卖平台（美团/饿了么/抖音），无支付方式
  - 订单明细: 每单 1~4 个菜品
  - 营业汇总: 每日每店聚合
  - 评论: 模拟各平台用户评论
  - 用户: 总部 + 员工 + 加盟商账号

使用方法:
  python generate_data.py

配置方式:
  1. 直接修改本脚本底部 CONFIG 字典
  2. 或设置环境变量 (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
"""

import os
import random
import time
from datetime import datetime, date, timedelta

# ============================================================
# 第三方依赖: pip install pymysql
# ============================================================
try:
    import pymysql
except ImportError:
    pymysql = None
    print("请先安装 pymysql: pip install pymysql")


# ============================================================
# 配置
# ============================================================
CONFIG = {
    "DB_HOST": os.getenv("DB_HOST", "localhost"),
    "DB_PORT": int(os.getenv("DB_PORT", "3306")),
    "DB_USER": os.getenv("DB_USER", "root"),
    "DB_PASSWORD": os.getenv("DB_PASSWORD", "liu12138"),
    "DB_NAME": os.getenv("DB_NAME", "for_student"),
    "START_DATE": "2024-01-01",
    "END_DATE": "2026-05-17",
    "STORE_COUNT": 500,
    "BATCH_ORDERS": 5000,       # orders 批量插入
    "BATCH_ITEMS": 10000,       # order_item 批量插入
    "BATCH_SUMMARY": 500,       # daily_summary 批量插入
    "BATCH_REVIEW": 500,        # review 批量插入
}

RANDOM_SEED = 42


# ============================================================
# 中国省市分布数据（500 家门店均匀分布）
# ============================================================
PROVINCE_CITY_DISTRIBUTION = [
    # ===== 华东地区 =====
    ("江苏", "南京市", 6), ("江苏", "苏州市", 5), ("江苏", "无锡市", 4), ("江苏", "常州市", 3), ("江苏", "南通市", 3),
    ("浙江", "杭州市", 6), ("浙江", "宁波市", 5), ("浙江", "温州市", 4), ("浙江", "嘉兴市", 3), ("浙江", "金华市", 3),
    ("山东", "济南市", 5), ("山东", "青岛市", 5), ("山东", "烟台市", 4), ("山东", "潍坊市", 3), ("山东", "临沂市", 3),
    ("安徽", "合肥市", 5), ("安徽", "芜湖市", 4), ("安徽", "蚌埠市", 3), ("安徽", "马鞍山市", 3), ("安徽", "安庆市", 3),
    ("福建", "福州市", 5), ("福建", "厦门市", 5), ("福建", "泉州市", 4), ("福建", "漳州市", 3), ("福建", "龙岩市", 2),
    ("江西", "南昌市", 5), ("江西", "赣州市", 4), ("江西", "九江市", 3), ("江西", "宜春市", 3),
    ("上海", "上海市", 12),
    # ===== 华南地区 =====
    ("广东", "广州市", 7), ("广东", "深圳市", 7), ("广东", "东莞市", 5), ("广东", "佛山市", 4),
    ("广东", "珠海市", 3), ("广东", "中山市", 3), ("广东", "惠州市", 3), ("广东", "汕头市", 3),
    ("广西", "南宁市", 5), ("广西", "柳州市", 4), ("广西", "桂林市", 4), ("广西", "北海市", 3),
    ("海南", "海口市", 4), ("海南", "三亚市", 3), ("海南", "琼海市", 2),
    # ===== 华中地区 =====
    ("河南", "郑州市", 6), ("河南", "洛阳市", 5), ("河南", "新乡市", 4), ("河南", "南阳市", 3), ("河南", "许昌市", 3),
    ("湖北", "武汉市", 6), ("湖北", "宜昌市", 4), ("湖北", "襄阳市", 4), ("湖北", "荆州市", 3), ("湖北", "黄石市", 3),
    ("湖南", "长沙市", 6), ("湖南", "株洲市", 4), ("湖南", "衡阳市", 4), ("湖南", "岳阳市", 3), ("湖南", "常德市", 3),
    # ===== 华北地区 =====
    ("河北", "石家庄市", 5), ("河北", "唐山市", 4), ("河北", "保定市", 4), ("河北", "邯郸市", 3), ("河北", "廊坊市", 3),
    ("山西", "太原市", 5), ("山西", "大同市", 4), ("山西", "运城市", 3), ("山西", "长治市", 3),
    ("内蒙古", "呼和浩特市", 4), ("内蒙古", "包头市", 3), ("内蒙古", "赤峰市", 3), ("内蒙古", "呼伦贝尔市", 2),
    ("北京", "北京市", 14),
    ("天津", "天津市", 8),
    # ===== 西南地区 =====
    ("四川", "成都市", 7), ("四川", "绵阳市", 5), ("四川", "德阳市", 4), ("四川", "宜宾市", 4),
    ("四川", "乐山市", 3), ("四川", "泸州市", 3),
    ("重庆", "重庆市", 12),
    ("云南", "昆明市", 5), ("云南", "大理市", 3), ("云南", "曲靖市", 3), ("云南", "丽江市", 2), ("云南", "红河市", 2),
    ("贵州", "贵阳市", 5), ("贵州", "遵义市", 4), ("贵州", "毕节市", 3), ("贵州", "六盘水市", 2),
    ("西藏", "拉萨市", 3), ("西藏", "日喀则市", 2),
    # ===== 西北地区 =====
    ("陕西", "西安市", 6), ("陕西", "咸阳市", 4), ("陕西", "宝鸡市", 3), ("陕西", "延安市", 3), ("陕西", "汉中市", 3),
    ("甘肃", "兰州市", 5), ("甘肃", "天水市", 3), ("甘肃", "酒泉市", 3), ("甘肃", "庆阳市", 3),
    ("宁夏", "银川市", 4), ("宁夏", "石嘴山市", 2), ("宁夏", "吴忠市", 2),
    ("青海", "西宁市", 4), ("青海", "海东市", 2), ("青海", "格尔木市", 2),
    ("新疆", "乌鲁木齐市", 5), ("新疆", "克拉玛依市", 2), ("新疆", "伊宁市", 2), ("新疆", "喀什市", 2),
    # ===== 东北地区 =====
    ("辽宁", "沈阳市", 5), ("辽宁", "大连市", 5), ("辽宁", "鞍山市", 3), ("辽宁", "锦州市", 3), ("辽宁", "丹东市", 2),
    ("吉林", "长春市", 5), ("吉林", "吉林市", 4), ("吉林", "延吉市", 3), ("吉林", "四平市", 2),
    ("黑龙江", "哈尔滨市", 5), ("黑龙江", "大庆市", 4), ("黑龙江", "齐齐哈尔市", 3), ("黑龙江", "牡丹江市", 3),
]

assert sum(c for _, _, c in PROVINCE_CITY_DISTRIBUTION) == 500

SUPPLIERS = [
    "鑫源食材供应有限公司", "绿源农产品批发", "鲜味达食品贸易公司",
    "悦丰蔬菜配送中心", "四季鲜供应链管理", "旺旺调味品商行",
    "隆达粮油贸易公司", "顺丰冷链物流", "本土优选农产品合作社",
    "永辉食材批发中心",
]

# ============================================================
# 会员姓名数据
# ============================================================
SURNAMES = ["王", "李", "张", "刘", "陈", "杨", "黄", "赵", "周", "吴",
            "徐", "孙", "马", "朱", "胡", "郭", "林", "何", "高", "罗"]

GIVEN_NAMES = ["伟", "芳", "娜", "秀英", "敏", "静", "丽", "强", "磊", "洋",
               "勇", "艳", "杰", "娟", "涛", "明", "超", "秀兰", "霞", "平",
               "刚", "桂英", "文", "华", "飞", "红", "斌", "玲", "军", "建华"]

# ============================================================
# 菜品数据（31 道）
# ============================================================
# (name, category, price, cost, spicy, popularity)
DISHES = [
    # 热菜
    ("红烧肉",       "热菜", 28.0, 16.0, 0, 90),
    ("宫保鸡丁",     "热菜", 22.0, 12.0, 2, 85),
    ("鱼香肉丝",     "热菜", 22.0, 11.0, 1, 88),
    ("麻婆豆腐",     "热菜", 12.0, 5.0,  2, 82),
    ("回锅肉",       "热菜", 24.0, 13.0, 1, 78),
    ("番茄炒蛋",     "热菜", 14.0, 6.0,  0, 92),
    ("酸辣土豆丝",   "热菜", 10.0, 4.0,  1, 85),
    ("青椒肉丝",     "热菜", 18.0, 9.0,  1, 80),
    ("水煮肉片",     "热菜", 26.0, 14.0, 3, 72),
    ("干锅花菜",     "热菜", 16.0, 8.0,  1, 75),
    ("小炒肉",       "热菜", 20.0, 11.0, 2, 78),
    ("红烧排骨",     "热菜", 32.0, 18.0, 0, 70),
    ("蒜蓉青菜",     "热菜", 12.0, 5.0,  0, 76),
    # 凉菜
    ("凉拌黄瓜",     "凉菜", 8.0,  3.0,  1, 70),
    ("皮蛋豆腐",     "凉菜", 10.0, 4.0,  0, 65),
    ("口水鸡",       "凉菜", 16.0, 8.0,  2, 60),
    ("凉拌木耳",     "凉菜", 10.0, 4.0,  1, 62),
    # 主食
    ("米饭",         "主食", 3.0,  1.0,  0, 99),
    ("馒头",         "主食", 2.0,  0.8,  0, 60),
    ("蛋炒饭",       "主食", 12.0, 5.0,  0, 75),
    ("炒面",         "主食", 14.0, 6.0,  0, 68),
    # 汤品
    ("紫菜蛋花汤",   "汤品", 6.0,  2.0,  0, 65),
    ("番茄蛋汤",     "汤品", 6.0,  2.0,  0, 60),
    ("酸辣汤",       "汤品", 8.0,  3.0,  1, 55),
    # 饮品
    ("可乐",         "饮品", 5.0,  2.0,  0, 50),
    ("雪碧",         "饮品", 5.0,  2.0,  0, 48),
    ("冰红茶",       "饮品", 5.0,  2.0,  0, 45),
    ("酸梅汤",       "饮品", 6.0,  2.5,  0, 55),
    # 配菜
    ("卤蛋",         "配菜", 3.0,  1.5,  0, 50),
    ("鸡腿",         "配菜", 8.0,  4.5,  0, 65),
    ("烤肠",         "配菜", 4.0,  2.0,  0, 45),
]

# ============================================================
# 节假日（2025 年）
# ============================================================
HOLIDAYS = {
    date(2025, 1, 1): ("元旦", 1.3),
    date(2025, 1, 28): ("除夕", 1.5),
    date(2025, 1, 29): ("春节初一", 1.6),
    date(2025, 1, 30): ("春节初二", 1.5),
    date(2025, 1, 31): ("春节初三", 1.5),
    date(2025, 2, 1): ("春节初四", 1.4),
    date(2025, 2, 2): ("春节初五", 1.4),
    date(2025, 2, 3): ("春节初六", 1.3),
    date(2025, 2, 4): ("春节初七", 1.3),
    date(2025, 4, 4): ("清明节", 1.2),
    date(2025, 4, 5): ("清明节", 1.3),
    date(2025, 4, 6): ("清明节", 1.2),
    date(2025, 5, 1): ("劳动节", 1.4),
    date(2025, 5, 2): ("劳动节", 1.4),
    date(2025, 5, 3): ("劳动节", 1.3),
    date(2025, 5, 4): ("劳动节", 1.3),
    date(2025, 5, 5): ("劳动节", 1.2),
    date(2025, 5, 31): ("端午节", 1.3),
    date(2025, 6, 1): ("端午节", 1.2),
    date(2025, 6, 2): ("端午节", 1.2),
    date(2025, 10, 1): ("国庆节&中秋节", 1.5),
    date(2025, 10, 2): ("国庆节", 1.5),
    date(2025, 10, 3): ("国庆节", 1.4),
    date(2025, 10, 4): ("国庆节", 1.4),
    date(2025, 10, 5): ("国庆节", 1.3),
    date(2025, 10, 6): ("中秋节", 1.4),
    date(2025, 10, 7): ("国庆节", 1.2),
    date(2025, 12, 31): ("跨年", 1.2),
    # 2026 年节日（截至 2026-05-17）
    date(2026, 1, 1): ("元旦", 1.3),
    date(2026, 2, 16): ("除夕", 1.5),
    date(2026, 2, 17): ("春节初一", 1.6),
    date(2026, 2, 18): ("春节初二", 1.5),
    date(2026, 2, 19): ("春节初三", 1.5),
    date(2026, 2, 20): ("春节初四", 1.4),
    date(2026, 2, 21): ("春节初五", 1.4),
    date(2026, 2, 22): ("春节初六", 1.3),
    date(2026, 2, 23): ("春节初七", 1.3),
    date(2026, 4, 5): ("清明节", 1.2),
    date(2026, 4, 6): ("清明节", 1.2),
    date(2026, 5, 1): ("劳动节", 1.4),
    date(2026, 5, 2): ("劳动节", 1.3),
    date(2026, 5, 3): ("劳动节", 1.2),
}

WEEKEND_MULTIPLIER = 1.12
SEASON_MULTIPLIERS = {1: 0.95, 2: 0.90, 3: 0.95, 4: 1.05, 5: 1.08, 6: 1.12,
                      7: 1.15, 8: 1.12, 9: 1.05, 10: 1.02, 11: 0.95, 12: 0.90}

WEATHER_OPTIONS = {
    "spring": [("晴", 0.35), ("多云", 0.30), ("阴", 0.15), ("雨", 0.15), ("暴雨", 0.05)],
    "summer": [("晴", 0.30), ("多云", 0.25), ("阴", 0.10), ("雨", 0.20), ("暴雨", 0.10), ("台风", 0.05)],
    "autumn": [("晴", 0.40), ("多云", 0.30), ("阴", 0.15), ("雨", 0.10), ("雾", 0.05)],
    "winter": [("晴", 0.30), ("多云", 0.25), ("阴", 0.15), ("雪", 0.10), ("雨夹雪", 0.05), ("雾霾", 0.15)],
}

# 订单时间分布权重（每半小时时段，8:00-21:00）
ORDER_TIME_DIST = [
    (8, 0, 0.02), (8, 30, 0.03),       # 早餐/早间
    (9, 0, 0.02), (9, 30, 0.02),
    (10, 0, 0.02), (10, 30, 0.03),
    (11, 0, 0.08), (11, 30, 0.12),      # 午餐高峰
    (12, 0, 0.12), (12, 30, 0.10),
    (13, 0, 0.05), (13, 30, 0.03),
    (14, 0, 0.02), (14, 30, 0.02),
    (15, 0, 0.02), (15, 30, 0.02),
    (16, 0, 0.02), (16, 30, 0.03),
    (17, 0, 0.05), (17, 30, 0.07),      # 晚餐高峰
    (18, 0, 0.08), (18, 30, 0.07),
    (19, 0, 0.05), (19, 30, 0.03),
    (20, 0, 0.02), (20, 30, 0.01),
]

# ============================================================
# 评论模板
# ============================================================
POSITIVE_REVIEWS = [
    "味道很好，经常来吃，{dish}特别推荐！",
    "份量足，价格实惠，物超所值！",
    "出餐速度很快，服务态度好。",
    "环境干净整洁，食材新鲜。",
    "整体不错，孩子很爱吃，下次还会来。",
    "性价比很高，工作餐首选。",
    "{dish}做得很好吃，味道正宗。",
    "外卖包装很严实，到手里还是热的。",
    "非常满意的一次用餐体验，推荐！",
    "老顾客了，品质一直很稳定。",
    "价格实惠分量足，一个人吃得很饱。",
    "高峰期出餐也很快，点赞！",
    "味道不错，环境也好，适合朋友小聚。",
    "餐厅卫生做得很好，吃得放心。",
    "新品很好吃，推荐大家尝鲜。",
]

NEUTRAL_REVIEWS = [
    "一般般，中规中矩，没有特别惊艳。",
    "{dish}味道还行，但价格偏贵了。",
    "出餐速度可以再快一点。",
    "环境还行，但高峰期有点吵。",
    "味道可以，但没有以前好吃了。",
    "外卖送得有点慢，希望能改进。",
    "普通快餐水平，不功不过。",
    "份量比以前少了，希望保持。",
    "菜品种类可以再多一些。",
    "偶尔吃一次还行，经常吃会腻。",
]

NEGATIVE_REVIEWS = [
    "{dish}味道太差了，完全不是那个味。",
    "等了很久才上菜，体验很差。",
    "价格涨了但份量反而少了，差评。",
    "外卖送错了菜品，太失望了。",
    "卫生状况堪忧，桌上有油渍。",
    "服务态度很差，爱答不理的。",
    "{dish}明显不新鲜，口感很奇怪。",
    "踩雷了，不会再来了。",
    "价格太贵了，这个价位不如去别的店。",
    "外卖包装太简陋，汤都洒了。",
]


# ============================================================
# 数据生成器
# ============================================================

class DataGenerator:
    """模拟数据生成器"""

    def __init__(self, config: dict):
        self.config = config
        self.rand = random.Random(RANDOM_SEED)
        self.conn = None
        self.cursor = None

        self.store_ids: list[int] = []
        self.dish_ids: list[int] = []
        # dish_id -> {name, price, category, popularity}
        self.dish_info: dict[int, dict] = {}

        # store_id -> list of member_ids
        self.member_ids: dict[int, list[int]] = {}

        self.start_date = date.fromisoformat(config["START_DATE"])
        self.end_date = date.fromisoformat(config["END_DATE"])
        self.total_days = (self.end_date - self.start_date).days + 1

        # store_id -> open_date（每家门店随机开业时间）
        self.store_dates: dict[int, date] = {}

        # 累计订单号计数器（全局唯一）
        self.order_no_counter = 1

    # --------------------------------------------------
    # 数据库连接
    # --------------------------------------------------
    def connect(self):
        if pymysql is None:
            raise ImportError("请先安装 pymysql: pip install pymysql")
        self.conn = pymysql.connect(
            host=self.config["DB_HOST"],
            port=self.config["DB_PORT"],
            user=self.config["DB_USER"],
            password=self.config["DB_PASSWORD"],
            database=self.config["DB_NAME"],
            charset="utf8mb4",
            autocommit=False,
        )
        self.cursor = self.conn.cursor()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def execute(self, sql: str, params: tuple | list | None = None):
        self.cursor.execute(sql, params or ())

    def executemany(self, sql: str, params_list: list[tuple]):
        self.cursor.executemany(sql, params_list)

    def commit(self):
        self.conn.commit()

    # --------------------------------------------------
    # 门店
    # --------------------------------------------------
    def generate_stores(self) -> list[dict]:
        print(f"  生成 {self.config['STORE_COUNT']} 家门店...")
        stores = []
        counter_map: dict[str, int] = {}
        for province, city, count in PROVINCE_CITY_DISTRIBUTION:
            for _ in range(count):
                key = f"{province}_{city}"
                counter_map[key] = counter_map.get(key, 0) + 1
                idx = counter_map[key]
                name = f"{province}{city[:-1]}{idx:03d}店"
                area_code = city[:-1]
                stores.append({
                    "name": name,
                    "province": province,
                    "city": city,
                    "district": f"{area_code}区",
                    "address": f"{city}模拟路{self.rand.randint(1, 500)}号",
                    "phone": f"1{self.rand.randint(30, 99)}{self.rand.randint(10000000, 99999999)}",
                    "open_date": date(2023, 7, 1) + timedelta(days=self.rand.randint(0, 913)),
                    "status": 1,
                    "level": self.rand.choices([1, 2, 3], weights=[10, 60, 30])[0],
                })
        return stores

    def insert_stores(self, stores: list[dict]) -> list[int]:
        sql = """INSERT INTO store (name, province, city, district, address, phone,
                                    open_date, status, level, created_at, updated_at)
                 VALUES (%(name)s, %(province)s, %(city)s, %(district)s, %(address)s,
                         %(phone)s, %(open_date)s, %(status)s, %(level)s, NOW(), NOW())"""
        ids = []
        for s in stores:
            self.execute(sql, s)
            ids.append(self.cursor.lastrowid)
        self.commit()
        print(f"    → 已插入 {len(ids)} 家门店, ID 范围: {ids[0]}~{ids[-1]}")
        return ids

    # --------------------------------------------------
    # 菜品
    # --------------------------------------------------
    def generate_and_insert_dishes(self) -> list[int]:
        print(f"  生成 {len(DISHES)} 道菜品...")
        sql = """INSERT INTO dish (name, category, price, cost, unit, spicy_level, popularity, status, created_at)
                 VALUES (%s, %s, %s, %s, %s, %s, %s, 1, NOW())"""
        self.executemany(sql, [
            (n, c, p, co, "份", s, pop) for n, c, p, co, s, pop in DISHES
        ])
        self.commit()
        self.execute("SELECT id, name, price, category, popularity FROM dish ORDER BY id")
        ids = []
        for r in self.cursor.fetchall():
            ids.append(r[0])
            self.dish_info[r[0]] = {
                "name": r[1], "price": float(r[2]),
                "category": r[3], "popularity": r[4],
            }
        print(f"    → 已插入 {len(ids)} 道菜品")
        return ids

    # --------------------------------------------------
    # 会员
    # --------------------------------------------------
    def generate_and_insert_members(self, store_ids: list[int], store_dates: dict[int, date]):
        print(f"\n  生成会员数据...")
        sql = """INSERT INTO member (store_id, name, phone, level, points, total_spent,
                                     total_orders, join_date, status, created_at)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())"""
        for sid in store_ids:
            n_members = self.rand.randint(30, 80)
            store_members = []
            open_date = store_dates[sid]
            store_days = (self.end_date - open_date).days + 1
            for _ in range(n_members):
                name = self.rand.choice(SURNAMES) + self.rand.choice(GIVEN_NAMES)
                phone = f"1{self.rand.randint(30, 99)}{self.rand.randint(10000000, 99999999)}"
                # 注册日期在门店开业后
                jd = open_date + timedelta(days=self.rand.randint(0, max(0, store_days - 1)))
                # 根据注册时长和活跃度生成累计消费
                days_since_join = (self.end_date - jd).days
                avg_order = self.rand.uniform(18, 35)
                freq = self.rand.uniform(0.03, 0.12)  # 日均消费概率
                total_orders = max(1, int(days_since_join * freq))
                total_spent = round(total_orders * avg_order, 2)
                # 等级
                if total_spent >= 5000:
                    level = 4
                elif total_spent >= 2000:
                    level = 3
                elif total_spent >= 500:
                    level = 2
                else:
                    level = 1
                points = int(total_spent * self.rand.uniform(0.5, 1.0))
                store_members.append((sid, name, phone, level, points, total_spent, total_orders, jd, 1))
            self.executemany(sql, store_members)
            self.commit()
            # 回查 member_id
            self.execute("SELECT id FROM member WHERE store_id = %s ORDER BY id", (sid,))
            self.member_ids[sid] = [r[0] for r in self.cursor.fetchall()]
        total = sum(len(v) for v in self.member_ids.values())
        print(f"    → 生成 {total} 条会员记录")

    # --------------------------------------------------
    # 天气/季节辅助
    # --------------------------------------------------
    def _get_season(self, month: int) -> str:
        if 3 <= month <= 5:
            return "spring"
        elif 6 <= month <= 8:
            return "summer"
        elif 9 <= month <= 11:
            return "autumn"
        return "winter"

    def _get_weather_and_temp(self, month: int) -> tuple[str, float]:
        season = self._get_season(month)
        opts = WEATHER_OPTIONS[season]
        weather = self.rand.choices([w for w, _ in opts], [p for _, p in opts])[0]
        temp_ranges = {"spring": (8, 22), "summer": (25, 38), "autumn": (10, 25), "winter": (-10, 10)}
        low, high = temp_ranges[season]
        return weather, round(self.rand.uniform(low, high), 1)

    def _calc_daily_params(self, store_id: int, d: date) -> dict | None:
        """计算单店单日营业参数，返回 None 表示休息"""
        store_level = ((store_id - 1) % 3) + 1
        store_seed = 0.8 + self.rand.random() * 0.4
        base_revenue = 1500 * store_seed
        level_mult = {1: 1.3, 2: 1.0, 3: 0.8}[store_level]

        weekday = d.weekday()
        day_of_week_mult = {0: 0.92, 1: 0.95, 2: 0.95, 3: 1.0, 4: 1.05, 5: 1.08, 6: 1.05}[weekday]
        weekday_mult = WEEKEND_MULTIPLIER if weekday >= 5 else 0.98

        holiday_mult = 1.0
        is_holiday = 0
        if d in HOLIDAYS:
            name, holiday_mult = HOLIDAYS[d]
            is_holiday = 1
            if "春节" in name and self.rand.random() < 0.1:
                return None

        season_mult = SEASON_MULTIPLIERS[d.month]
        weather, temp = self._get_weather_and_temp(d.month)
        weather_mult = {"暴雨": 0.75, "台风": 0.75, "暴雪": 0.75, "雨": 0.90, "雪": 0.90, "雾霾": 0.85}.get(weather, 1.0)

        total_mult = level_mult * weekday_mult * day_of_week_mult * holiday_mult * season_mult * weather_mult
        revenue = base_revenue * total_mult * self.rand.uniform(0.88, 1.12)
        revenue = max(500, round(revenue, 2))

        avg_price = round(self.rand.uniform(22, 38), 1)
        # 外卖占比 15%~40%
        takeout_ratio = self.rand.uniform(0.15, 0.40)
        order_count = max(1, int(revenue / avg_price))

        return {
            "store_id": store_id,
            "date": d,
            "revenue": revenue,
            "avg_price": avg_price,
            "order_count": order_count,
            "takeout_ratio": takeout_ratio,
            "is_holiday": is_holiday,
            "weather": weather,
            "temperature": temp,
            "weekday": weekday,
        }

    # --------------------------------------------------
    # 订单生成（核心）
    # --------------------------------------------------
    def _generate_orders_for_day(self, params: dict) -> tuple[list[dict], list[dict], list[dict]]:
        """
        为单店单天生成堂食订单、外卖订单及明细。
        返回 (dine_in_orders, takeout_orders, items)
        """
        sid = params["store_id"]
        d = params["date"]
        order_count = params["order_count"]
        takeout_ratio = params["takeout_ratio"]
        dish_ids = self.dish_ids
        dish_count = len(dish_ids)
        pop_weights = [self.dish_info[did]["popularity"] for did in dish_ids]

        # 该门店的会员列表
        members = self.member_ids.get(sid, [])

        dine_in_orders: list[dict] = []
        takeout_orders: list[dict] = []
        items: list[dict] = []

        for _ in range(order_count):
            # 菜品数量 1~4
            n_dishes = self.rand.choices([1, 2, 3, 4], weights=[15, 35, 33, 17])[0]

            # 按 popularity 加权选菜（允许重复）
            selected_dish_ids = self.rand.choices(dish_ids, weights=pop_weights, k=n_dishes)

            total = 0.0
            order_items = []
            for did in selected_dish_ids:
                info = self.dish_info[did]
                # 价格微浮动 ±8%
                price = round(info["price"] * self.rand.uniform(0.94, 1.06), 1)
                qty = 1
                amount = round(price * qty, 2)
                total += amount
                order_items.append({
                    "dish_id": did,
                    "dish_name": info["name"],
                    "quantity": qty,
                    "price": price,
                    "amount": amount,
                })

            total = round(total, 2)

            # 分配时间
            time_idx = self.rand.choices(range(len(ORDER_TIME_DIST)),
                                          weights=[p for _, _, p in ORDER_TIME_DIST])[0]
            h, m, _ = ORDER_TIME_DIST[time_idx]
            m_offset = self.rand.randint(0, 29)
            order_time = datetime(d.year, d.month, d.day, h, m + m_offset)

            order_no = f"ORD{d.strftime('%Y%m%d')}{self.order_no_counter:08d}"
            self.order_no_counter += 1

            # 判断订单类型
            is_takeout = self.rand.random() < takeout_ratio

            if is_takeout:
                platform = self.rand.choice(["美团", "饿了么", "抖音"])
                takeout_orders.append({
                    "store_id": sid,
                    "order_no": order_no,
                    "total_amount": total,
                    "platform": platform,
                    "dish_count": n_dishes,
                    "order_time": order_time,
                })
            else:
                pay_method = self.rand.choices(
                    ["微信支付", "支付宝支付", "现金支付"], weights=[50, 35, 15]
                )[0]
                # 50% 概率是会员订单
                member_id = None
                if members and self.rand.random() < 0.5:
                    member_id = self.rand.choice(members)
                dine_in_orders.append({
                    "store_id": sid,
                    "order_no": order_no,
                    "total_amount": total,
                    "payment_method": pay_method,
                    "member_id": member_id,
                    "dish_count": n_dishes,
                    "order_time": order_time,
                })

            for oi in order_items:
                oi["store_id"] = sid
                oi["order_no"] = order_no

            items.extend(order_items)

        return dine_in_orders, takeout_orders, items

    # --------------------------------------------------
    # 批量插入订单
    # --------------------------------------------------
    def _insert_dine_in_orders_batch(self, orders: list[dict]) -> dict[str, int]:
        """批量插入堂食订单，返回 {order_no -> id} 映射"""
        if not orders:
            return {}
        sql = """INSERT INTO dine_in_order (store_id, order_no, total_amount, payment_method,
                                            member_id, dish_count, order_time, created_at)
                 VALUES (%(store_id)s, %(order_no)s, %(total_amount)s, %(payment_method)s,
                         %(member_id)s, %(dish_count)s, %(order_time)s, NOW())"""
        self.executemany(sql, orders)
        order_nos = [o["order_no"] for o in orders]
        placeholders = ",".join(["%s"] * len(order_nos))
        self.execute(f"SELECT order_no, id FROM dine_in_order WHERE order_no IN ({placeholders})", order_nos)
        return {row[0]: row[1] for row in self.cursor.fetchall()}

    def _insert_takeout_orders_batch(self, orders: list[dict]) -> dict[str, int]:
        """批量插入外卖订单，返回 {order_no -> id} 映射"""
        if not orders:
            return {}
        sql = """INSERT INTO takeout_order (store_id, order_no, total_amount, platform,
                                            dish_count, order_time, created_at)
                 VALUES (%(store_id)s, %(order_no)s, %(total_amount)s, %(platform)s,
                         %(dish_count)s, %(order_time)s, NOW())"""
        self.executemany(sql, orders)
        order_nos = [o["order_no"] for o in orders]
        placeholders = ",".join(["%s"] * len(order_nos))
        self.execute(f"SELECT order_no, id FROM takeout_order WHERE order_no IN ({placeholders})", order_nos)
        return {row[0]: row[1] for row in self.cursor.fetchall()}

    def _insert_items_batch(self, items: list[dict], no_to_id: dict[str, int]):
        """批量插入订单明细"""
        if not items:
            return
        sql = """INSERT INTO order_item (order_id, store_id, dish_id, dish_name,
                                         quantity, price, amount)
                 VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        rows = []
        for it in items:
            oid = no_to_id.get(it["order_no"])
            if oid:
                rows.append((
                    oid, it["store_id"], it["dish_id"], it["dish_name"],
                    it["quantity"], it["price"], it["amount"],
                ))
        if rows:
            self.executemany(sql, rows)

    def _aggregate_summary(self, params: dict, dine_in: list[dict], takeout: list[dict], items: list[dict]) -> dict:
        """从堂食和外卖订单聚合出 daily_summary"""
        all_orders = dine_in + takeout
        total_revenue = sum(o["total_amount"] for o in all_orders)
        total_orders = len(all_orders)
        dine_in_rev = sum(o["total_amount"] for o in dine_in)
        takeout_rev = sum(o["total_amount"] for o in takeout)
        avg_price = round(total_revenue / total_orders, 2) if total_orders else 0
        dish_total = len(items)

        peak_rev = 0.0
        for o in all_orders:
            if 11 <= o["order_time"].hour < 13 or 18 <= o["order_time"].hour < 20:
                peak_rev += o["total_amount"]
        peak_rev = round(peak_rev, 2)

        return {
            "store_id": params["store_id"],
            "summary_date": params["date"],
            "total_revenue": total_revenue,
            "total_orders": total_orders,
            "total_customers": total_orders,
            "avg_price": avg_price,
            "dine_in_revenue": dine_in_rev,
            "takeout_revenue": takeout_rev,
            "peak_hour_revenue": peak_rev,
            "dish_total_count": dish_total,
            "is_holiday": params["is_holiday"],
            "weather": params["weather"],
            "temperature": params["temperature"],
        }

    def process_store(self, store_id: int, open_date: date) -> tuple[int, int, int, int]:
        """处理一个门店从开业到结束所有天的数据，返回 (堂食订单数, 外卖订单数, 总明细数)"""
        total_dine_in = 0
        total_takeout = 0
        total_items = 0
        store_days = (self.end_date - open_date).days + 1

        for day_offset in range(store_days):
            d = open_date + timedelta(days=day_offset)
            params = self._calc_daily_params(store_id, d)
            if params is None:
                continue

            dine_in, takeout, items = self._generate_orders_for_day(params)

            # 插入堂食订单
            no_to_id = {}
            no_to_id.update(self._insert_dine_in_orders_batch(dine_in))
            # 插入外卖订单
            no_to_id.update(self._insert_takeout_orders_batch(takeout))
            # 插入明细
            self._insert_items_batch(items, no_to_id)

            # 插入汇总
            summary = self._aggregate_summary(params, dine_in, takeout, items)
            self.execute("""
                INSERT INTO daily_summary (store_id, summary_date, total_revenue, total_orders,
                    total_customers, avg_price, dine_in_revenue, takeout_revenue,
                    peak_hour_revenue, dish_total_count, is_holiday, weather, temperature, created_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
            """, (
                summary["store_id"], summary["summary_date"], summary["total_revenue"],
                summary["total_orders"], summary["total_customers"], summary["avg_price"],
                summary["dine_in_revenue"], summary["takeout_revenue"],
                summary["peak_hour_revenue"], summary["dish_total_count"],
                summary["is_holiday"], summary["weather"], summary["temperature"],
            ))

            total_dine_in += len(dine_in)
            total_takeout += len(takeout)
            total_items += len(items)

        self.commit()
        return total_dine_in, total_takeout, total_items

    # --------------------------------------------------
    # 评论
    # --------------------------------------------------
    def generate_and_insert_reviews(self, store_ids: list[int], store_dates: dict[int, date]):
        print(f"\n  生成评论数据...")
        sql = """INSERT INTO review (store_id, platform, rating, content, review_date,
                 review_time, tags, is_replied, reply_content, is_positive, created_at)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())"""
        dish_names = [d[0] for d in DISHES]
        all_reviews = []
        for sid in store_ids:
            open_date = store_dates[sid]
            store_days = (self.end_date - open_date).days + 1
            review_days = max(1, int(store_days * 0.15))
            rdates = set()
            for _ in range(review_days):
                rd = open_date + timedelta(days=self.rand.randint(0, store_days - 1))
                rdates.add(rd)
            for rd in rdates:
                rating = self.rand.choices([1, 2, 3, 4, 5], weights=[30, 10, 5, 15, 40])[0]
                platform = self.rand.choice(["美团", "饿了么", "大众点评"])
                if rating >= 4:
                    template = self.rand.choice(POSITIVE_REVIEWS)
                    is_pos = 1
                elif rating == 3:
                    template = self.rand.choice(NEUTRAL_REVIEWS)
                    is_pos = 0
                else:
                    template = self.rand.choice(NEGATIVE_REVIEWS)
                    is_pos = -1
                content = template.replace("{dish}", self.rand.choice(dish_names))
                tag_map = {"味道": ["口味赞", "味道好", "很下饭", "味道一般", "不好吃"],
                           "服务": ["服务好", "出餐快", "态度差", "上菜慢"],
                           "分量": ["份量足", "量大实惠", "份量少", "不够吃"],
                           "卫生": ["干净", "环境好", "卫生差"]}
                tc = self.rand.choice(list(tag_map.keys()))
                tags = ",".join(self.rand.sample(tag_map[tc], self.rand.randint(1, 3)))
                need_reply = False
                reply = None
                if is_pos == 1 and self.rand.random() < 0.7:
                    need_reply = True
                    reply = self.rand.choice(["感谢您的评价，欢迎再次光临！", "谢谢您的支持，我们会继续努力！", "感谢您的喜爱，祝您生活愉快！"])
                elif is_pos == -1 and self.rand.random() < 0.9:
                    need_reply = True
                    reply = self.rand.choice([
                        "非常抱歉给您带来不好的体验，我们会立即整改，欢迎您再次光临监督。",
                        "感谢您的反馈，我们会加强管理，提升菜品质量和服务水平。",
                        "对不起让您失望了，我们会认真反思改进，期待您的再次光临。",
                    ])
                rt = datetime(rd.year, rd.month, rd.day, self.rand.randint(8, 21), self.rand.randint(0, 59))
                all_reviews.append((sid, platform, rating, content, rd, rt, tags,
                                    1 if need_reply else 0, reply, is_pos))
        batch = self.config["BATCH_REVIEW"]
        for i in range(0, len(all_reviews), batch):
            self.executemany(sql, all_reviews[i:i + batch])
            self.commit()
        print(f"    → 生成 {len(all_reviews)} 条评论")

    # --------------------------------------------------
    # 用户
    # --------------------------------------------------
    def generate_and_insert_users(self, store_ids: list[int]):
        print(f"\n  生成用户数据...")
        self.execute("DELETE FROM user")
        sql = """INSERT INTO user (username, password_hash, display_name, role, store_id, phone, email, status, created_at)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,1,NOW())"""
        pw = "pbkdf2:sha256:1000000$simulated$dummyhash"
        self.execute(sql, ("boss", pw, "管理员", "boss", None, "13800000000", "boss@ric.com"))
        for i in range(1, 6):
            self.execute(sql, (f"employee{i}", pw, f"员工{i}", "employee", None, f"1380000000{i}", f"employee{i}@ric.com"))
        for sid in store_ids:
            self.execute("SELECT name FROM store WHERE id=%s", (sid,))
            row = self.cursor.fetchone()
            sn = row[0] if row else f"门店{sid}"
            self.execute(sql, (f"store{sid}", pw, f"{sn}_管理员", "franchisee", sid,
                               f"1{self.rand.randint(30,99)}{self.rand.randint(10000000,99999999)}",
                               f"store{sid}@ric.com"))
        self.commit()
        self.execute("SELECT role,COUNT(*) FROM user GROUP BY role")
        for r in self.cursor.fetchall():
            print(f"    → {r[0]}: {r[1]} 个账号")

    # --------------------------------------------------
    # 主流程
    # --------------------------------------------------
    def run(self):
        print("=" * 60)
        print("  连锁餐饮 AI 系统 - 模拟数据生成")
        print(f"  数据库: {self.config['DB_HOST']}:{self.config['DB_PORT']}/{self.config['DB_NAME']}")
        print(f"  日期范围: {self.config['START_DATE']} ~ {self.config['END_DATE']}")
        print(f"  门店数量: {self.config['STORE_COUNT']}")
        print("=" * 60)
        t_start = time.time()

        # ── 1. 门店 ──
        print("\n[1/5] 门店数据")
        store_data = self.generate_stores()
        store_ids = self.insert_stores(store_data)
        # 记录每家门店的开业日期
        self.store_dates = {sid: sd["open_date"] for sid, sd in zip(store_ids, store_data)}

        # ── 2. 菜品 ──
        print("\n[2/5] 菜品数据")
        self.generate_and_insert_dishes()

        # ── 3. 订单 + 营业数据（最耗时）──
        print(f"\n[3/5] 订单数据（{len(store_ids)} 家门店，每家经营 1~2 年）")
        grand_total_dine_in = 0
        grand_total_takeout = 0
        grand_total_items = 0
        store_idx = 0
        for sid in store_ids:
            store_idx += 1
            di, to, items = self.process_store(sid, self.store_dates[sid])
            grand_total_dine_in += di
            grand_total_takeout += to
            grand_total_items += items
            if store_idx % 50 == 0 or store_idx == len(store_ids):
                pct = store_idx / len(store_ids) * 100
                print(f"    门店进度: {pct:.0f}% ({store_idx}/{len(store_ids)}), "
                      f"已生成订单: {grand_total_dine_in + grand_total_takeout}, "
                      f"明细: {grand_total_items}")

        # ── 4. 评论 ──
        print("\n[4/5] 风评评论数据")
        self.generate_and_insert_reviews(store_ids, self.store_dates)

        # ── 5. 用户 ──
        print("\n[5/5] 用户账号")
        self.generate_and_insert_users(store_ids)

        # ── 统计 ──
        elapsed = time.time() - t_start
        print(f"\n{'=' * 60}")
        print(f"  ✓ 数据生成完成！耗时: {elapsed:.1f} 秒")
        self.execute("SELECT COUNT(*) FROM dine_in_order")
        r1 = self.cursor.fetchone()[0]
        self.execute("SELECT COUNT(*) FROM takeout_order")
        r2 = self.cursor.fetchone()[0]
        self.execute("SELECT COUNT(*) FROM order_item")
        r3 = self.cursor.fetchone()[0]
        self.execute("SELECT COUNT(*) FROM daily_summary")
        r4 = self.cursor.fetchone()[0]
        print(f"  ✓ 门店: {len(store_ids)} 家")
        print(f"  ✓ 菜品: {len(self.dish_ids)} 道")
        print(f"  ✓ 堂食订单: {r1} 条")
        print(f"  ✓ 外卖订单: {r2} 条")
        print(f"  ✓ 订单明细: {r3} 条")
        print(f"  ✓ 营业汇总: {r4} 条")
        print(f"{'=' * 60}")


if __name__ == "__main__":
    generator = DataGenerator(CONFIG)
    try:
        generator.connect()
        generator.run()
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        generator.close()
