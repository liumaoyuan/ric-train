#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
遍历数据库中所有英雄，爬取对应网页获取详情并插入表中
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
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

from Base.Repository.register import register_default_connection, register_game_helper_connection
from GameHelper.crawler.lolHeroDetailCrawler import LOLHeroDetailCrawler
from GameHelper.models.gameHeroDetailModel import GameHeroDetailModel
from GameHelper.models.gameEntityModel import GameEntityModel


def crawl_all_hero_details():
    """遍历数据库中所有英雄，爬取详情并存储"""
    print("\n" + "=" * 60)
    print("  遍历数据库中所有英雄，爬取详情并存储")
    print("=" * 60 + "\n")

    # 注册数据库连接
    register_default_connection()
    register_game_helper_connection()

    crawler = LOLHeroDetailCrawler()

    # 获取物品数据（用于出装推荐）
    print("正在获取物品列表...")
    crawler.fetch_items()

    # 从数据库获取所有英雄
    print("\n正在获取数据库中的英雄列表...")
    heroes = GameEntityModel.get_by_type(entity_type="hero", game_name="英雄联盟", status=1, limit=1000)

    if not heroes:
        print("未找到任何英雄数据，请先运行 crawlAllHeroes.py 爬取英雄列表")
        return

    print(f"共找到 {len(heroes)} 个英雄\n")

    saved_count = 0
    skip_count = 0
    error_count = 0
    error_details = []

    for hero in heroes:
        hero_name = hero.entity_name
        hero_id = hero.entity_code

        print(f"[{saved_count + skip_count + error_count + 1}/{len(heroes)}] 处理：{hero_name} (ID: {hero_id})")

        # 检查是否已存在详情
        existing = GameHeroDetailModel.get_by_hero_id(hero_id, "英雄联盟")
        if existing:
            skip_count += 1
            print(f"  - 已存在，跳过")
            continue

        # 获取英雄详情
        hero_detail = crawler.fetch_hero_detail(hero_id)

        if not hero_detail:
            error_count += 1
            error_details.append(f"{hero_name} (ID: {hero_id}) - 获取详情失败")
            print(f"  - 获取详情失败")
            time.sleep(0.1)
            continue

        try:
            # 解析数据
            parsed_data = crawler.parse_hero_for_detail(hero_detail)

            # 创建英雄详情记录
            detail = GameHeroDetailModel(
                hero_id=hero_id,
                game_name="英雄联盟",
                hero_name=parsed_data['hero_name'],
                hero_alias=parsed_data.get('hero_alias'),
                hero_title=parsed_data.get('hero_title'),
                roles=parsed_data.get('roles'),
                camp=parsed_data.get('camp'),
                damage_type=parsed_data.get('damage_type'),
                hp=parsed_data.get('hp'),
                hp_per_level=parsed_data.get('hp_per_level'),
                mp=parsed_data.get('mp'),
                mp_per_level=parsed_data.get('mp_per_level'),
                attack_damage=parsed_data.get('attack_damage'),
                attack_damage_per_level=parsed_data.get('attack_damage_per_level'),
                attack_speed=parsed_data.get('attack_speed'),
                attack_speed_per_level=parsed_data.get('attack_speed_per_level'),
                armor=parsed_data.get('armor'),
                armor_per_level=parsed_data.get('armor_per_level'),
                magic_resist=parsed_data.get('magic_resist'),
                magic_resist_per_level=parsed_data.get('magic_resist_per_level'),
                move_speed=parsed_data.get('move_speed'),
                attack_range=parsed_data.get('attack_range'),
                hp_regen=parsed_data.get('hp_regen'),
                mp_regen=parsed_data.get('mp_regen'),
                attack_rating=parsed_data.get('attack_rating'),
                defense_rating=parsed_data.get('defense_rating'),
                magic_rating=parsed_data.get('magic_rating'),
                difficulty_rating=parsed_data.get('difficulty_rating'),
                mobility_rating=parsed_data.get('mobility_rating'),
                utility_rating=parsed_data.get('utility_rating'),
                crowd_control_rating=parsed_data.get('crowd_control_rating'),
                skill_order=parsed_data.get('skill_order'),
                skill_max_order=parsed_data.get('skill_max_order'),
                starting_items=json.dumps(parsed_data.get('starting_items'), ensure_ascii=False) if parsed_data.get('starting_items') else None,
                core_items=json.dumps(parsed_data.get('core_items'), ensure_ascii=False) if parsed_data.get('core_items') else None,
                boots_recommendation=json.dumps(parsed_data.get('boots_recommendation'), ensure_ascii=False) if parsed_data.get('boots_recommendation') else None,
                summoner_spells=json.dumps(parsed_data.get('summoner_spells'), ensure_ascii=False) if parsed_data.get('summoner_spells') else None,
                ally_tips=json.dumps(parsed_data.get('ally_tips'), ensure_ascii=False) if parsed_data.get('ally_tips') else None,
                enemy_tips=json.dumps(parsed_data.get('enemy_tips'), ensure_ascii=False) if parsed_data.get('enemy_tips') else None,
                skin_count=parsed_data.get('skin_count', 0),
                status=1,
            )
            detail.save()
            saved_count += 1
            print(f"  - 保存成功")

        except Exception as e:
            error_count += 1
            error_details.append(f"{hero_name} (ID: {hero_id}) - {str(e)}")
            print(f"  - 保存失败：{e}")

        # 避免请求过快
        time.sleep(0.05)

    # 打印统计信息
    print("\n" + "=" * 60)
    print("  爬取完成")
    print("=" * 60)
    print(f"  总数：{len(heroes)}")
    print(f"  新保存：{saved_count}")
    print(f"  已跳过：{skip_count}")
    print(f"  失败：{error_count}")

    if error_details:
        print("\n失败详情:")
        for detail in error_details:
            print(f"  - {detail}")


if __name__ == '__main__':
    crawl_all_hero_details()
