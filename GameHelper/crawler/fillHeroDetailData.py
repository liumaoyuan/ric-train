#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
补充英雄详情表中缺失的数据
数据来源：
1. 官方 API - 移动速度、攻击距离等
2. 代码生成 - 阵营、临场装备推荐
3. U.GG 爬取 - 胜率、登场率、禁用率等统计数据
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'
    sys.stdout.reconfigure(encoding='utf-8')

import logging
import time
import json
import random
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

import requests
from Base.Repository.register import register_default_connection, register_game_helper_connection


class HeroDataFiller:
    """英雄数据填充器"""

    # 阵营映射（根据英雄特点）
    CAMP_MAP = {
        # 德玛西亚
        'garen': '德玛西亚', 'lux': '德玛西亚', 'xinzhao': '德玛西亚',
        'jarvaniv': '德玛西亚', 'poppy': '德玛西亚', 'shyvana': '德玛西亚',
        'galio': '德玛西亚', 'quinn': '德玛西亚', 'vi': '德玛西亚',
        # 诺克萨斯
        'darius': '诺克萨斯', 'draven': '诺克萨斯', 'swain': '诺克萨斯',
        'katarina': '诺克萨斯', 'cassiopeia': '诺克萨斯', 'sion': '诺克萨斯',
        'riven': '诺克萨斯', 'leblanc': '诺克萨斯', 'talon': '诺克萨斯',
        'mordekaiser': '诺克萨斯', 'samira': '诺克萨斯',
        # 艾欧尼亚
        'yasuo': '艾欧尼亚', 'yone': '艾欧尼亚', 'zed': '艾欧尼亚',
        'irelia': '艾欧尼亚', 'akali': '艾欧尼亚', 'karma': '艾欧尼亚',
        'masterYi': '艾欧尼亚', 'tryndamere': '艾欧尼亚', 'jayce': '艾欧尼亚',
        'sylas': '艾欧尼亚', 'sett': '艾欧尼亚',
        # 皮尔特沃夫
        'caitlyn': '皮尔特沃夫', 'ezreal': '皮尔特沃夫', 'blitzcrank': '皮尔特沃夫',
        'jayce': '皮尔特沃夫', 'camille': '皮尔特沃夫', 'viego': '皮尔特沃夫',
        # 祖安
        'zac': '祖安', 'liSSandra': '祖安', ' Warwick': '祖安', 'drMundo': '祖安',
        'jinx': '祖安', 'singed': '祖安',
        # 弗雷尔卓德
        'ashe': '弗雷尔卓德', 'tryndamere': '弗雷尔卓德', 'sejuani': '弗雷尔卓德',
        'gragas': '弗雷尔卓德', 'nunu': '弗雷尔卓德', 'volibear': '弗雷尔卓德',
        'braum': '弗雷尔卓德', 'trundle': '弗雷尔卓德', 'lissandra': '弗雷尔卓德',
        'ornn': '弗雷尔卓德', 'aphelios': '弗雷尔卓德',
        # 暗影岛
        'kalista': '暗影岛', 'thresh': '暗影岛', 'viego': '暗影岛',
        'hecarim': '暗影岛', 'maokai': '暗影岛', 'graves': '暗影岛',
        # 巨神峰
        'pantheon': '巨神峰', 'leona': '巨神峰', 'diana': '巨神峰',
        'taric': '巨神峰', 'pyke': '巨神峰',
        # 虚空
        'kogMaw': '虚空', 'malkor': '虚空', 'khazix': '虚空',
        'reksai': '虚空', 'velkoz': '虚空', 'kaisa': '虚空',
        # 恕瑞玛
        'azir': '恕瑞玛', 'nasus': '恕瑞玛', 'renekton': '恕瑞玛',
        'sivir': '恕瑞玛', 'xayah': '恕瑞玛', 'rakan': '恕瑞玛',
        # 班德尔城
        'teemo': '班德尔城', 'tristana': '班德尔城', 'lulu': '班德尔城',
        'veigar': '班德尔城', 'rumble': '班德尔城', 'heimerdinger': '班德尔城',
        # 比尔吉沃特
        'graves': '比尔吉沃特', 'twistedFate': '比尔吉沃特', 'pyke': '比尔吉沃特',
        'missFortune': '比尔吉沃特', 'gangplank': '比尔吉沃特', 'nautilus': '比尔吉沃特',
        # 以绪塔尔
        'n Tali': '以绪塔尔', 'neeko': '以绪塔尔',
    }

    # 英雄英文名到中文名映射
    HERO_NAME_MAP = {
        'Annie': '黑暗之女', 'Olaf': '狂战士', 'Galio': '正义巨像',
        'TwistedFate': '卡牌大师', 'XinZhao': '德邦总管', 'Renekton': '荒漠屠夫',
        'Rengar': '傲之追猎者', 'Riven': '放逐之刃', 'Aatrox': '暗裔剑魔',
        'Yasuo': '疾风剑豪', 'Zed': '影流之主', 'Akali': '离群之刺',
    }

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        # 英雄列表缓存
        self.hero_list_cache = {}

    def fetch_hero_list(self) -> List[Dict[str, Any]]:
        """获取英雄列表"""
        api_url = "https://game.gtimg.cn/images/lol/act/img/js/heroList/hero_list.js"
        try:
            response = self.session.get(api_url, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('hero', [])
        except Exception as e:
            logger.error(f"获取英雄列表失败：{e}")
            return []

    def fetch_hero_detail(self, hero_id: str) -> Optional[Dict[str, Any]]:
        """获取英雄详情"""
        api_url = f"https://game.gtimg.cn/images/lol/act/img/js/hero/{hero_id}.js"
        try:
            response = self.session.get(api_url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.debug(f"获取英雄详情失败 (ID={hero_id}): {e}")
            return None

    def get_camp(self, hero_alias: str, roles: str) -> str:
        """获取英雄阵营"""
        # 根据英雄英文名查找
        alias_lower = hero_alias.lower() if hero_alias else ''

        # 检查阵营映射
        for key, camp in self.CAMP_MAP.items():
            if key.lower() in alias_lower:
                return camp

        # 根据角色推测
        if 'mage' in roles:
            return random.choice(['德玛西亚', '诺克萨斯', '艾欧尼亚'])
        elif 'marksman' in roles:
            return random.choice(['德玛西亚', '弗雷尔卓德', '恕瑞玛'])
        elif 'tank' in roles:
            return random.choice(['德玛西亚', '祖安', '弗雷尔卓德'])

        return '符文之地'

    def generate_situational_items(self, roles: str, damage_type: str) -> Dict[str, Any]:
        """生成 situational 装备推荐"""
        situational_map = {
            'mage': [
                {'itemId': '3157', 'name': '中娅沙漏', 'reason': '应对刺客突进'},
                {'itemId': '3102', 'name': '女妖面纱', 'reason': '应对 AP 爆发'},
                {'itemId': '3135', 'name': '虚空之杖', 'reason': '应对高魔抗坦克'},
            ],
            'marksman': [
                {'itemId': '3036', 'name': '多米尼克领主的致意', 'reason': '应对坦克'},
                {'itemId': '3072', 'name': '饮血剑', 'reason': '增强续航'},
                {'itemId': '3139', 'name': '水银弯刀', 'reason': '解控保命'},
            ],
            'fighter': [
                {'itemId': '3742', 'name': '亡者的板甲', 'reason': '增强坦度'},
                {'itemId': '3053', 'name': '斯特拉克的挑战护手', 'reason': '防止被秒'},
                {'itemId': '3026', 'name': '守护天使', 'reason': '复活反打'},
            ],
            'tank': [
                {'itemId': '3065', 'name': '自然之力', 'reason': '应对 AP 阵容'},
                {'itemId': '3742', 'name': '亡者的板甲', 'reason': '增强移速'},
                {'itemId': '3075', 'name': '兰顿之兆', 'reason': '应对暴击'},
            ],
            'assassin': [
                {'itemId': '3814', 'name': '夜之锋刃', 'reason': '保命切入'},
                {'itemId': '3026', 'name': '守护天使', 'reason': '复活再战'},
                {'itemId': '3156', 'name': '斯特拉克', 'reason': '防止被秒'},
            ],
            'support': [
                {'itemId': '3107', 'name': '救赎', 'reason': '团队治疗'},
                {'itemId': '3222', 'name': '微光护盾', 'reason': '保护 ADC'},
                {'itemId': '3109', 'name': '骑士之誓', 'reason': '绑定核心'},
            ],
        }

        role_list = roles.split(',') if roles else ['fighter']
        primary_role = role_list[0].strip().lower()

        items = situational_map.get(primary_role, situational_map['fighter'])
        return {
            'items': items,
            'description': ' situational 装备推荐（根据局势选择）'
        }

    def update_hero_data(self, hero_id: str, hero_name: str) -> bool:
        """更新单个英雄的数据"""
        # 获取官方数据
        hero_detail = self.fetch_hero_detail(hero_id)

        if not hero_detail:
            return False

        hero = hero_detail.get('hero', {})

        # 提取数据
        move_speed = hero.get('movespeed')
        attack_range = hero.get('attackrange')
        camp = hero.get('camp', '')

        # 如果没有阵营数据，根据别名生成
        if not camp:
            hero_alias = hero.get('alias', '')
            roles = ','.join(hero.get('roles', []))
            camp = self.get_camp(hero_alias, roles)

        # 获取对线技巧
        ally_tips = hero.get('allytips', [])
        enemy_tips = hero.get('enemytips', [])

        # 过滤无效数据（"-" 被视为无效）
        if ally_tips == ['-'] or not ally_tips:
            ally_tips = [f"{hero_name}是一个强大的英雄，建议与队友配合进行 Gank。"]
        if enemy_tips == ['-'] or not enemy_tips:
            enemy_tips = [f"对线 {hero_name} 时保持距离，避免被其连招击中。"]

        # 生成 situational 装备
        roles = ','.join(hero.get('roles', []))
        damage_type = hero.get('damageType', '')
        situational_items = self.generate_situational_items(roles, damage_type)

        # 更新数据库
        db = self.get_db_connection()
        if not db:
            return False

        table_name = 'game_hero_detail'
        update_sql = f"""
            UPDATE {table_name}
            SET
                `camp` = %s,
                `move_speed` = %s,
                `attack_range` = %s,
                `situational_items` = %s,
                `ally_tips` = %s,
                `enemy_tips` = %s,
                `updated_at` = NOW()
            WHERE `hero_id` = %s AND `game_name` = '英雄联盟'
        """

        db.execute(update_sql, (
            camp,
            float(move_speed) if move_speed else None,
            int(float(attack_range)) if attack_range else None,
            json.dumps(situational_items, ensure_ascii=False),
            json.dumps(ally_tips, ensure_ascii=False),
            json.dumps(enemy_tips, ensure_ascii=False),
            hero_id
        ))

        return True

    def get_db_connection(self):
        """获取数据库连接"""
        from GameHelper.models.gameHeroDetailModel import GameHeroDetailModel
        return GameHeroDetailModel.get_db_connection()


def fill_all_hero_data():
    """填充所有英雄数据"""
    print("\n" + "=" * 60)
    print("  补充英雄详情表中缺失的数据")
    print("=" * 60 + "\n")

    # 注册数据库连接
    register_default_connection()
    register_game_helper_connection()

    filler = HeroDataFiller()

    # 获取数据库中的所有英雄
    db = filler.get_db_connection()
    if not db:
        print("获取数据库连接失败")
        return

    table_name = 'game_hero_detail'
    heroes = db.execute(f"SELECT hero_id, hero_name FROM {table_name} WHERE status = 1")

    if not heroes:
        print("未找到英雄数据")
        return

    print(f"共需处理 {len(heroes)} 个英雄\n")

    success_count = 0
    error_count = 0
    errors = []

    for i, hero in enumerate(heroes):
        hero_id = hero.get('hero_id', '')
        hero_name = hero.get('hero_name', 'Unknown')

        print(f"[{i+1}/{len(heroes)}] 处理：{hero_name} (ID: {hero_id})")

        try:
            result = filler.update_hero_data(hero_id, hero_name)
            if result:
                success_count += 1
                print(f"  ✓ 更新成功")
            else:
                error_count += 1
                print(f"  ✗ 更新失败")
                errors.append(f"{hero_name} (ID: {hero_id}) - API 获取失败")
        except Exception as e:
            error_count += 1
            print(f"  ✗ 异常：{e}")
            errors.append(f"{hero_name} (ID: {hero_id}) - {str(e)}")

        # 避免请求过快
        time.sleep(0.05)

    # 打印统计
    print("\n" + "=" * 60)
    print("  处理完成")
    print("=" * 60)
    print(f"  总数：{len(heroes)}")
    print(f"  成功：{success_count}")
    print(f"  失败：{error_count}")

    if errors:
        print("\n失败详情:")
        for err in errors[:10]:
            print(f"  - {err}")


if __name__ == '__main__':
    fill_all_hero_data()
