#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成英雄统计数据（胜率、登场率、禁用率等）
基于英雄角色定位生成合理的模拟数据
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'
    sys.stdout.reconfigure(encoding='utf-8')

import logging
import random
import json
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

from Base.Repository.register import register_default_connection, register_game_helper_connection


class HeroStatsGenerator:
    """英雄统计数据生成器"""

    # 各位置胜率基准
    WINRATE_BASE = {
        'mage': 50.5,
        'marksman': 49.8,
        'fighter': 50.2,
        'tank': 51.0,
        'assassin': 49.5,
        'support': 50.0,
    }

    # 各位置登场率基准 (%)
    PICKRATE_BASE = {
        'mage': 12.0,
        'marksman': 15.0,
        'fighter': 18.0,
        'tank': 8.0,
        'assassin': 10.0,
        'support': 10.0,
    }

    # 各位置禁用率基准 (%)
    BANRATE_BASE = {
        'mage': 8.0,
        'marksman': 12.0,
        'fighter': 15.0,
        'tank': 5.0,
        'assassin': 20.0,
        'support': 6.0,
    }

    # 优势/劣势对线推荐
    COUNTER_MAP = {
        'mage': {
            'strong': ['squishy', 'immobile'],
            'weak': ['assassin', 'fighter'],
        },
        'marksman': {
            'strong': ['tank', 'squishy'],
            'weak': ['assassin', 'mage'],
        },
        'fighter': {
            'strong': ['mage', 'squishy'],
            'weak': ['tank', 'marksman'],
        },
        'tank': {
            'strong': ['fighter', 'marksman'],
            'weak': ['mage', 'true damage'],
        },
        'assassin': {
            'strong': ['mage', 'marksman'],
            'weak': ['tank', 'fighter'],
        },
        'support': {
            'strong': ['squishy', 'engage'],
            'weak': ['assassin', 'poke'],
        },
    }

    # 英雄类型映射
    HERO_TYPES = {
        '1': ['mage', 'support'],  # 黑暗之女
        '157': ['fighter', 'assassin'],  # 疾风剑豪
        '67': ['marksman', 'assassin'],  # 暗夜猎手
    }

    def __init__(self):
        pass

    def generate_stats(self, roles: str, damage_type: str, hero_name: str) -> Dict[str, Any]:
        """生成英雄统计数据"""
        role_list = [r.strip().lower() for r in roles.split(',')] if roles else ['fighter']
        primary_role = role_list[0]

        # 生成胜率 (45%-55% 范围)
        base_winrate = self.WINRATE_BASE.get(primary_role, 50.0)
        winrate = base_winrate + random.uniform(-3, 3)
        winrate = max(45.0, min(55.0, winrate))

        # 生成登场率 (5%-25% 范围)
        base_pickrate = self.PICKRATE_BASE.get(primary_role, 10.0)
        pickrate = base_pickrate + random.uniform(-5, 10)
        pickrate = max(5.0, min(25.0, pickrate))

        # 生成禁用率 (0%-30% 范围)
        base_banrate = self.BANRATE_BASE.get(primary_role, 5.0)
        banrate = base_banrate + random.uniform(-3, 15)
        banrate = max(0.0, min(30.0, banrate))

        # 生成出场次数 (基于登场率)
        # 假设总场次 100000
        total_games = 100000
        games_played = int(pickrate / 100 * total_games)

        # 生成优势/劣势对线
        strong_against = self._generate_counter_text(primary_role, 'strong')
        weak_against = self._generate_counter_text(primary_role, 'weak')

        return {
            'pick_rate': round(pickrate, 2),
            'win_rate': round(winrate, 2),
            'ban_rate': round(banrate, 2),
            'games_played': games_played,
            'strong_against': strong_against,
            'weak_against': weak_against,
        }

    def _generate_counter_text(self, role: str, type: str) -> str:
        """生成对线建议文本"""
        if type == 'strong':
            counters = self.COUNTER_MAP.get(role, {}).get('strong', [])
            descriptions = {
                'squishy': '脆皮英雄',
                'immobile': '无位移英雄',
                'tank': '坦克英雄',
                'marksman': '射手英雄',
                'mage': '法师英雄',
                'assassin': '刺客英雄',
                'fighter': '战士英雄',
                'engage': '开团型英雄',
                'poke': '消耗型英雄',
                'true damage': '真实伤害英雄',
            }
        else:
            counters = self.COUNTER_MAP.get(role, {}).get('weak', [])
            descriptions = {
                'squishy': '脆皮英雄',
                'immobile': '无位移英雄',
                'tank': '坦克英雄',
                'marksman': '射手英雄',
                'mage': '法师英雄',
                'assassin': '刺客英雄',
                'fighter': '战士英雄',
                'engage': '开团型英雄',
                'poke': '消耗型英雄',
                'true damage': '真实伤害英雄',
            }

        counter_texts = [descriptions.get(c, c) for c in counters]
        if counter_texts:
            return '、'.join(counter_texts)
        return '视对线情况而定'


def fill_stats_data():
    """填充统计数据"""
    print("\n" + "=" * 60)
    print("  生成英雄统计数据")
    print("=" * 60 + "\n")

    # 注册数据库连接
    register_default_connection()
    register_game_helper_connection()

    generator = HeroStatsGenerator()

    # 获取数据库中的所有英雄
    from GameHelper.models.gameHeroDetailModel import GameHeroDetailModel
    db = GameHeroDetailModel.get_db_connection()
    if not db:
        print("获取数据库连接失败")
        return

    table_name = 'game_hero_detail'
    heroes = db.execute(f"SELECT hero_id, hero_name, roles, damage_type FROM {table_name} WHERE status = 1 ORDER BY hero_id")

    if not heroes:
        print("未找到英雄数据")
        return

    print(f"共需处理 {len(heroes)} 个英雄\n")

    success_count = 0
    error_count = 0

    for i, hero in enumerate(heroes):
        hero_id = hero.get('hero_id', '')
        hero_name = hero.get('hero_name', 'Unknown')
        roles = hero.get('roles', '')
        damage_type = hero.get('damage_type', '')

        print(f"[{i+1}/{len(heroes)}] 处理：{hero_name} (ID: {hero_id})")

        try:
            # 生成统计数据
            stats = generator.generate_stats(roles, damage_type, hero_name)

            # 更新数据库
            update_sql = f"""
                UPDATE {table_name}
                SET
                    `pick_rate` = %s,
                    `win_rate` = %s,
                    `ban_rate` = %s,
                    `games_played` = %s,
                    `strong_against` = %s,
                    `weak_against` = %s,
                    `updated_at` = NOW()
                WHERE `hero_id` = %s AND `game_name` = '英雄联盟'
            """

            db.execute(update_sql, (
                stats['pick_rate'],
                stats['win_rate'],
                stats['ban_rate'],
                stats['games_played'],
                stats['strong_against'],
                stats['weak_against'],
                hero_id
            ))

            success_count += 1
            print(f"  ✓ 胜率：{stats['win_rate']}%, 登场率：{stats['pick_rate']}%, 禁用率：{stats['ban_rate']}%")

        except Exception as e:
            error_count += 1
            print(f"  ✗ 错误：{e}")

    # 打印统计
    print("\n" + "=" * 60)
    print("  处理完成")
    print("=" * 60)
    print(f"  总数：{len(heroes)}")
    print(f"  成功：{success_count}")
    print(f"  失败：{error_count}")


if __name__ == '__main__':
    fill_stats_data()
