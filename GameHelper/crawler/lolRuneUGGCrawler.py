#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从 u.gg 爬取英雄联盟符文数据 - 只获取推荐的一套
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'
    sys.stdout.reconfigure(encoding='utf-8')

import logging
import json
import re
from typing import Dict, Any, Optional, List, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

import requests
from bs4 import BeautifulSoup


class UGGCrawler:
    """从 u.gg 爬取符文数据"""

    RUNE_TREE_IDS = {
        'Precision': 8000,
        'Domination': 8100,
        'Sorcery': 8200,
        'Resolve': 8400,
        'Inspiration': 8300,
    }

    SHARD_MAPPING = {
        'AdaptiveForce': 5005,
        'AdaptiveForcePlus': 5008,
        'AttackSpeed': 5001,
        'Armor': 5002,
        'MagicResist': 5003,
        'HealthScaling': 5007,
        'AbilityHaste': 5004,
    }

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def fetch_champion_runes(self, champion_name: str) -> Optional[Dict[str, Any]]:
        """从 u.gg 获取英雄符文数据"""
        logger.info(f"尝试从 u.gg 获取 {champion_name} 的符文数据...")
        try:
            url = f"https://u.gg/lol/champions/{champion_name}/build"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            return self._parse_html(response.text)

        except Exception as e:
            logger.error(f"从 u.gg 获取失败：{e}")
        return None

    def _parse_html(self, html: str) -> Optional[Dict[str, Any]]:
        """解析 u.gg HTML 获取符文数据 - 只获取推荐的一套"""
        soup = BeautifulSoup(html, 'html.parser')

        # 1. 查找主符文树和副符文树
        tree_headers = soup.find_all(class_='rune-tree_header')
        trees = [el.get_text(strip=True) for el in tree_headers]

        primary_tree = trees[0] if len(trees) >= 1 else None
        secondary_tree = trees[1] if len(trees) >= 2 else None

        if not primary_tree:
            return None

        # 2. 查找推荐的符文组合
        # u.gg 有一个特定的容器包含推荐的符文
        recommended_section = soup.find(class_='recommended-build')
        if not recommended_section:
            recommended_section = soup

        # 3. 从推荐区域查找符文图片
        primary_runes = []
        secondary_runes = []
        stat_shards = []

        # 查找主系符文树容器
        primary_tree_container = recommended_section.find(class_='primary-tree')
        if primary_tree_container:
            # 查找该容器下的所有符文图片
            perk_imgs = primary_tree_container.find_all('img', src=re.compile(r'small-perk-images'))
            for img in perk_imgs[:4]:  # 主系最多 4 个符文（包括 Keystone）
                src = img.get('src', '')
                match = re.search(r'/Styles/\w+/(\w+)/\1\.png', src)
                if match and match.group(1) not in primary_runes:
                    primary_runes.append(match.group(1))

        # 查找副系符文树容器
        secondary_tree_container = recommended_section.find(class_='rune-tree')
        if secondary_tree_container and secondary_tree_container != primary_tree_container:
            perk_imgs = secondary_tree_container.find_all('img', src=re.compile(r'small-perk-images'))
            for img in perk_imgs[:2]:  # 副系最多 2 个符文
                src = img.get('src', '')
                match = re.search(r'/Styles/\w+/(\w+)/\1\.png', src)
                if match and match.group(1) not in primary_runes:
                    secondary_runes.append(match.group(1))

        # 4. 如果没有找到，使用备用方法
        if not primary_runes:
            all_perk_imgs = recommended_section.find_all('img', src=re.compile(r'small-perk-images'))
            perk_names = []
            for img in all_perk_imgs:
                src = img.get('src', '')
                match = re.search(r'/Styles/\w+/(\w+)/\1\.png', src)
                if match:
                    perk_names.append(match.group(1))

            # 去重
            seen = set()
            unique_perks = []
            for p in perk_names:
                if p not in seen:
                    seen.add(p)
                    unique_perks.append(p)

            primary_runes = unique_perks[:4]
            secondary_runes = unique_perks[4:6]

        # 5. 查找符文碎片
        shard_container = recommended_section.find(class_='rune-tree stat-shards-container')
        if shard_container:
            shard_imgs = shard_container.find_all('img', src=re.compile(r'stat-icon'))
            for img in shard_imgs[:3]:
                src = img.get('src', '')
                match = re.search(r'stat-icon-(\w+)\.png', src)
                if match:
                    stat_shards.append(match.group(1))

        # 6. 构建返回数据
        result = {
            'primary_tree': primary_tree,
            'primary_tree_id': self.RUNE_TREE_IDS.get(primary_tree),
            'secondary_tree': secondary_tree,
            'secondary_tree_id': self.RUNE_TREE_IDS.get(secondary_tree) if secondary_tree else None,
            'primary_runes': primary_runes,
            'secondary_runes': secondary_runes,
            'shards': stat_shards,
            'shard_ids': [self.SHARD_MAPPING.get(s, 0) for s in stat_shards],
        }

        return result

    def format_rune_data_for_db(self, result: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """格式化符文数据为数据库 JSON 格式"""
        if not result:
            return {'primary_runes': None, 'secondary_runes': None, 'shards': None}

        # 主系符文
        primary_data = None
        if result.get('primary_tree') and result.get('primary_runes'):
            primary_data = {
                'tree': result['primary_tree'],
                'tree_id': result['primary_tree_id'],
                'runes': result['primary_runes']
            }

        # 副系符文
        secondary_data = None
        if result.get('secondary_tree') and result.get('secondary_runes'):
            secondary_data = {
                'tree': result['secondary_tree'],
                'tree_id': result['secondary_tree_id'],
                'runes': result['secondary_runes']
            }

        # 符文碎片
        shards_data = None
        if result.get('shards') or result.get('shard_ids'):
            shards_data = {
                'shards': list(zip(result.get('shard_ids', []), result.get('shards', [])))
            }

        return {
            'primary_runes': json.dumps(primary_data, ensure_ascii=False) if primary_data else None,
            'secondary_runes': json.dumps(secondary_data, ensure_ascii=False) if secondary_data else None,
            'shards': json.dumps(shards_data, ensure_ascii=False) if shards_data else None,
        }


def test_ugg():
    """测试 u.gg 爬虫"""
    crawler = UGGCrawler()

    test_heroes = [
        ('annie', '黑暗之女'),
        ('yasuo', '疾风剑豪'),
        ('vayne', '暗夜猎手'),
    ]

    for hero_en, hero_cn in test_heroes:
        print(f"\n{'='*60}")
        print(f"测试：{hero_cn} ({hero_en})")
        print('='*60)

        result = crawler.fetch_champion_runes(hero_en)
        if result:
            print(f"✓ 获取成功")
            print(f"  主系：{result.get('primary_tree')} (ID: {result.get('primary_tree_id')})")
            print(f"  主系符文：{result.get('primary_runes')}")
            print(f"  副系：{result.get('secondary_tree')} (ID: {result.get('secondary_tree_id')})")
            print(f"  副系符文：{result.get('secondary_runes')}")
            print(f"  碎片：{result.get('shards')}")

            # 格式化数据库格式
            db_format = crawler.format_rune_data_for_db(result)
            print(f"\n  数据库格式:")
            print(f"    primary_runes: {db_format.get('primary_runes')}")
            print(f"    secondary_runes: {db_format.get('secondary_runes')}")
            print(f"    shards: {db_format.get('shards')}")
        else:
            print(f"✗ 获取失败")


if __name__ == '__main__':
    test_ugg()
