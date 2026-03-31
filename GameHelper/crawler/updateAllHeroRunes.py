#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
遍历数据库中所有英雄，生成符文推荐并更新到数据库
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
from GameHelper.models.gameHeroDetailModel import GameHeroDetailModel
from GameHelper.models.gameEntityModel import GameEntityModel
from GameHelper.crawler.lolRuneGenerator import RuneGenerator


def update_all_hero_runes():
    """遍历数据库中所有英雄，生成符文推荐并更新"""
    print("\n" + "=" * 60)
    print("  遍历数据库中所有英雄，生成符文推荐并更新")
    print("=" * 60 + "\n")

    # 注册数据库连接
    register_default_connection()
    register_game_helper_connection()

    generator = RuneGenerator()

    # 从数据库获取所有英雄详情
    print("正在获取数据库中的英雄详情列表...")

    # 查询所有英雄详情
    db = GameHeroDetailModel.get_db_connection()
    if not db:
        print("获取数据库连接失败")
        return

    table_name = GameHeroDetailModel.get_table_name_with_db()
    heroes = db.execute(f"SELECT * FROM {table_name} WHERE `status` = 1 ORDER BY `hero_name`")

    if not heroes:
        print("未找到任何英雄数据")
        return

    print(f"共找到 {len(heroes)} 个英雄\n")

    updated_count = 0
    skip_count = 0
    error_count = 0
    error_details = []

    for hero_data in heroes:
        hero_name = hero_data.get('hero_name', 'Unknown')
        hero_id = hero_data.get('hero_id', '')
        roles_str = hero_data.get('roles', '')
        damage_type = hero_data.get('damage_type', '')

        # 解析角色定位
        roles = [r.strip().lower() for r in roles_str.split(',') if r.strip()] if roles_str else []

        print(f"[{updated_count + skip_count + error_count + 1}/{len(heroes)}] 处理：{hero_name} (ID: {hero_id})")
        print(f"  角色：{roles}, 伤害类型：{damage_type}")

        # 生成符文推荐
        try:
            rune_result = generator.generate_runes(roles, damage_type)

            # 格式化为数据库 JSON
            db_format = generator.format_for_db(rune_result)

            # 检查是否已有符文数据
            existing_primary = hero_data.get('primary_runes')

            if existing_primary:
                print(f"  - 已有符文数据，跳过更新")
                skip_count += 1
                continue

            # 更新数据库
            update_sql = f"""
                UPDATE {table_name}
                SET `primary_runes` = %s,
                    `secondary_runes` = %s,
                    `shards` = %s,
                    `updated_at` = NOW()
                WHERE `hero_id` = %s AND `game_name` = '英雄联盟'
            """

            db.execute(update_sql, (
                db_format['primary_runes'],
                db_format['secondary_runes'],
                db_format['shards'],
                hero_id
            ))

            updated_count += 1
            print(f"  - 更新成功：主系={rune_result['primary_tree']}, 副系={rune_result['secondary_tree']}")

        except Exception as e:
            error_count += 1
            error_details.append(f"{hero_name} (ID: {hero_id}) - {str(e)}")
            print(f"  - 更新失败：{e}")

        # 避免过快
        time.sleep(0.01)

    # 打印统计信息
    print("\n" + "=" * 60)
    print("  更新完成")
    print("=" * 60)
    print(f"  总数：{len(heroes)}")
    print(f"  已更新：{updated_count}")
    print(f"  已跳过：{skip_count}")
    print(f"  失败：{error_count}")

    if error_details:
        print("\n失败详情:")
        for detail in error_details:
            print(f"  - {detail}")


if __name__ == '__main__':
    update_all_hero_runes()
