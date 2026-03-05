#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
爬取所有英雄联盟英雄到数据库
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'
    sys.stdout.reconfigure(encoding='utf-8')

import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

from GameHelper.crawler.lolHeroCrawler import LOLHeroCrawler
from GameHelper.models.gameEntityModel import GameEntityModel


def crawl_all_heroes():
    """爬取所有英雄到数据库"""
    print("\n" + "=" * 60)
    print("  爬取英雄联盟英雄到数据库")
    print("=" * 60 + "\n")

    crawler = LOLHeroCrawler()
    heroes = crawler.fetch_hero_list()

    if not heroes:
        print("获取英雄列表失败")
        return

    saved_count = 0
    skip_count = 0
    error_count = 0

    print(f"开始爬取 {len(heroes)} 个英雄...\n")

    for hero in heroes:
        hero_name = hero.get('name', '')
        hero_id = str(hero.get('heroId', ''))

        # 检查是否已存在
        existing = GameEntityModel.get_by_entity_code(hero_id, "英雄联盟")
        if existing:
            skip_count += 1
            continue

        # 获取英雄详情
        hero_detail = crawler.fetch_hero_detail(hero_id)

        if hero_detail:
            h = hero_detail.get('hero', {})
            roles = ', '.join(h.get('roles', []))

            # 创建实体
            entity = GameEntityModel(
                entity_name=hero_name,
                entity_code=hero_id,
                entity_type="hero",
                game_name="英雄联盟",
                aliases=h.get('alias', ''),
                description=f"{h.get('title', '')} - {roles}",
                status=1
            )
            entity.save()
            saved_count += 1
            print(f"  已保存：{hero_name} ({roles})")
        else:
            error_count += 1

        # 避免请求过快
        time.sleep(0.05)

    print(f"\n爬取完成:")
    print(f"  新保存：{saved_count} 个英雄")
    print(f"  已跳过：{skip_count} 个英雄")
    print(f"  失败：{error_count} 个英雄")


if __name__ == '__main__':
    crawl_all_heroes()
