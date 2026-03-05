#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
英雄联盟官网数据爬虫
爬取英雄信息和攻略数据
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# 设置标准输出为 UTF-8
if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'
    sys.stdout.reconfigure(encoding='utf-8')

import logging
import time
import requests
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class LOLHeroCrawler:
    """英雄联盟英雄数据爬虫"""

    # API 端点
    HERO_LIST_API = "https://game.gtimg.cn/images/lol/act/img/js/heroList/hero_list.js"
    HERO_DETAIL_API = "https://game.gtimg.cn/images/lol/act/img/js/hero/{hero_id}.js"
    SKILL_DETAIL_API = "https://game.gtimg.cn/images/lol/act/img/js/skill/{skill_key}.js"

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Referer': 'https://lol.qq.com/',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch_hero_list(self) -> List[Dict[str, Any]]:
        """
        获取英雄列表

        Returns:
            英雄列表数据
        """
        logger.info("正在获取英雄列表...")

        try:
            response = self.session.get(self.HERO_LIST_API, timeout=30)
            response.raise_for_status()

            data = response.json()
            heroes = data.get('hero', [])

            logger.info(f"成功获取 {len(heroes)} 个英雄")
            return heroes

        except Exception as e:
            logger.error(f"获取英雄列表失败：{e}")
            return []

    def fetch_hero_detail(self, hero_id: str) -> Optional[Dict[str, Any]]:
        """
        获取英雄详情

        Args:
            hero_id: 英雄 ID

        Returns:
            英雄详情数据
        """
        api_url = self.HERO_DETAIL_API.format(hero_id=hero_id)

        try:
            response = self.session.get(api_url, timeout=30)
            response.raise_for_status()

            data = response.json()
            logger.info(f"成功获取英雄详情：{data.get('hero', {}).get('name', 'Unknown')}")
            return data

        except Exception as e:
            logger.error(f"获取英雄详情失败 (ID={hero_id}): {e}")
            return None

    def fetch_all_heroes_detail(self, hero_ids: Optional[List[str]] = None, delay: float = 0.1) -> List[Dict[str, Any]]:
        """
        批量获取所有英雄详情

        Args:
            hero_ids: 英雄 ID 列表，如果为 None 则获取全部
            delay: 请求间隔时间（秒）

        Returns:
            英雄详情列表
        """
        if hero_ids is None:
            hero_list = self.fetch_hero_list()
            hero_ids = [str(h['heroId']) for h in hero_list]

        heroes_detail = []

        for i, hero_id in enumerate(hero_ids, 1):
            logger.info(f"正在获取英雄 {i}/{len(hero_ids)}: ID={hero_id}")

            detail = self.fetch_hero_detail(hero_id)
            if detail:
                heroes_detail.append(detail)

            if delay > 0:
                time.sleep(delay)

        return heroes_detail

    def get_hero_image_url(self, hero_id: str, image_type: str = 'avatar') -> str:
        """
        获取英雄图片 URL

        Args:
            hero_id: 英雄 ID
            image_type: 图片类型 (avatar/small/medium/large/skin)

        Returns:
            图片 URL
        """
        base_url = "https://game.gtimg.cn/images/lol/act/img/"

        image_paths = {
            'avatar': f"hero/{hero_id}.png",
            'small': f"hero/{hero_id}.png",
            'medium': f"hero/{hero_id}.png",
            'large': f"hero/{hero_id}.png",
            'skin': f"hero/skin/{hero_id}.jpg",
        }

        return base_url + image_paths.get(image_type, image_paths['avatar'])

    def parse_hero_for_strategy(self, hero_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析英雄数据为攻略格式

        Args:
            hero_data: 英雄原始数据

        Returns:
            攻略格式的数据
        """
        hero = hero_data.get('hero', {})
        spells = hero_data.get('spells', [])

        # 提取基本信息
        result = {
            'hero_id': hero.get('heroId', ''),
            'hero_name': hero.get('name', ''),
            'hero_title': hero.get('title', ''),
            'hero_aliases': hero.get('alias', ''),
            'roles': hero.get('roles', []),
            'attack_type': hero.get('attacktype', 0),
            'damage_type': hero.get('damagetype', 0),
            'difficulty': hero.get('difficulty', {}),
            'stats': hero.get('stats', {}),
            'skills': [],
            'spells': [],
            'skins': hero.get('skins', []),
        }

        # 解析技能
        for spell in spells:
            skill_info = {
                'key': spell.get('spellKey', ''),
                'name': spell.get('name', ''),
                'description': spell.get('description', ''),
                'cooldown': spell.get('cooldown', []),
                'cost': spell.get('cost', []),
            }
            result['skills'].append(skill_info)

        return result


def test_crawler():
    """测试爬虫功能"""
    print("\n" + "=" * 60)
    print("  英雄联盟英雄数据爬虫测试")
    print("=" * 60 + "\n")

    crawler = LOLHeroCrawler()

    # 1. 获取英雄列表
    print("阶段 1: 获取英雄列表")
    print("-" * 40)
    heroes = crawler.fetch_hero_list()

    if heroes:
        print(f"\n共获取到 {len(heroes)} 个英雄")
        print("\n前 10 个英雄:")
        for i, hero in enumerate(heroes[:10], 1):
            print(f"  {i}. {hero['name']} (ID: {hero['heroId']})")

    # 2. 获取单个英雄详情
    print("\n" + "=" * 60)
    print("阶段 2: 获取单个英雄详情")
    print("-" * 40)

    test_hero_id = "1"  # 黑暗之女
    hero_detail = crawler.fetch_hero_detail(test_hero_id)

    if hero_detail:
        hero = hero_detail.get('hero', {})
        print(f"\n英雄名称：{hero.get('name', 'Unknown')}")
        print(f"英雄标题：{hero.get('title', '')}")
        print(f"英雄别名：{hero.get('alias', '')}")
        print(f"攻击类型：{'远程' if hero.get('attacktype') == 1 else '近战'}")
        print(f"伤害类型：{'物理' if hero.get('damagetype') == 1 else '魔法' if hero.get('damagetype') == 2 else '混合'}")

        # 显示技能
        spells = hero_detail.get('spells', [])
        print(f"\n技能列表:")
        for spell in spells:
            print(f"  {spell.get('spellKey')}: {spell.get('name', 'Unknown')}")
            print(f"     描述：{spell.get('description', '')[:100]}...")

    # 3. 解析为攻略格式
    print("\n" + "=" * 60)
    print("阶段 3: 解析为攻略格式")
    print("-" * 40)

    if hero_detail:
        strategy_data = crawler.parse_hero_for_strategy(hero_detail)

        print(f"\n攻略数据:")
        print(f"  英雄 ID: {strategy_data['hero_id']}")
        print(f"  英雄名称：{strategy_data['hero_name']}")
        print(f"  角色定位：{', '.join(strategy_data['roles'])}")
        print(f"  技能数量：{len(strategy_data['skills'])}")
        print(f"  皮肤数量：{len(strategy_data['skins'])}")

    print("\n" + "=" * 60)
    print("  爬虫测试完成")
    print("=" * 60 + "\n")


def crawl_heroes_to_database():
    """爬取英雄数据并存储到数据库"""
    from GameHelper.services.gameStrategyService import GameEntityService
    from GameHelper.models.gameEntityModel import GameEntityModel

    print("\n" + "=" * 60)
    print("  爬取英雄数据并存储到数据库")
    print("=" * 60 + "\n")

    crawler = LOLHeroCrawler()

    # 获取英雄列表
    heroes = crawler.fetch_hero_list()

    if not heroes:
        print("获取英雄列表失败")
        return

    saved_count = 0
    skip_count = 0

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

            # 创建实体
            entity = GameEntityModel(
                entity_name=hero_name,
                entity_code=hero_id,
                entity_type="hero",
                game_name="英雄联盟",
                aliases=h.get('alias', ''),
                description=f"{h.get('title', '')} - {h.get('alias', '')}",
                status=1
            )
            entity.save()
            saved_count += 1
            print(f"✓ 已保存：{hero_name}")

            # 避免请求过快
            time.sleep(0.05)

    print(f"\n爬取完成:")
    print(f"  新保存：{saved_count} 个英雄")
    print(f"  已跳过：{skip_count} 个英雄")


if __name__ == '__main__':
    import requests

    # 运行测试
    test_crawler()

    # 如果要爬取所有英雄到数据库，取消下面这行的注释
    # crawl_heroes_to_database()
