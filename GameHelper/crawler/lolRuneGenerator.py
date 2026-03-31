#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
英雄联盟符文生成器 - 基于英雄属性生成符文推荐
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

if sys.platform == 'win32':
    os.environ['PYTHONUTF8'] = '1'
    sys.stdout.reconfigure(encoding='utf-8')

import logging
import json
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class RuneGenerator:
    """基于英雄属性生成符文推荐"""

    # 符文碎片 ID 映射
    SHARD_MAPPING = {
        'AdaptiveForce': 5005,
        'AdaptiveForcePlus': 5008,
        'AttackSpeed': 5001,
        'Armor': 5002,
        'MagicResist': 5003,
        'HealthScaling': 5007,
        'AbilityHaste': 5004,
    }

    # 符文树 ID 映射
    RUNE_TREE_IDS = {
        'Precision': 8000,
        'Domination': 8100,
        'Sorcery': 8200,
        'Resolve': 8400,
        'Inspiration': 8300,
    }

    # 基石符文推荐（根据角色定位）
    KEYSTONE_MAP = {
        'mage': ('Sorcery', ['ArcaneComet', 'PhaseRush']),
        'marksman': ('Precision', ['LethalTempo', 'FleetFootwork', 'PressTheAttack']),
        'fighter': ('Precision', ['Conqueror', 'PressTheAttack']),
        'tank': ('Resolve', ['GraspOfTheUndying', 'Aftershock', 'Guardian']),
        'assassin': ('Domination', ['Electrocute', 'DarkHarvest']),
        'support': ('Sorcery', ['SummonAery', 'Guardian']),
        'jungle': ('Domination', ['Electrocute', 'DarkHarvest', 'Conqueror']),
    }

    # 主系符文推荐（按树分类）
    PRIMARY_RUNES = {
        'Precision': ['PresenceOfMind', 'LegendAlacrity', 'LegendHaste', 'CoupDeGrace', 'CutDown'],
        'Domination': ['CheapShot', 'SuddenImpact', 'EyeballCollection', 'UltimateHunter', 'RelentlessHunter'],
        'Sorcery': ['ManaflowBand', 'NullifyingOrb', 'Transcendence', 'Celerity', 'AbsoluteFocus', 'Scorch'],
        'Resolve': ['Demolish', 'FontOfLife', 'Conditioning', 'BonePlating', 'Overgrowth', 'Revitalize'],
        'Inspiration': ['MagicalFootwear', 'BiscuitDelivery', 'CosmicInsight', 'ApproachVelocity'],
    }

    # 副系符文推荐
    SECONDARY_PAIRINGS = {
        'Precision': ['Domination', 'Sorcery', 'Resolve'],
        'Domination': ['Sorcery', 'Precision'],
        'Sorcery': ['Domination', 'Inspiration', 'Precision'],
        'Resolve': ['Precision', 'Domination'],
        'Inspiration': ['Sorcery', 'Domination'],
    }

    # 符文碎片推荐（按角色）
    SHARD_MAP = {
        'mage': ['AdaptiveForcePlus', 'AdaptiveForce', 'MagicResist'],
        'marksman': ['AttackSpeed', 'AdaptiveForce', 'Armor'],
        'fighter': ['AttackSpeed', 'AdaptiveForce', 'Armor'],
        'tank': ['AttackSpeed', 'Armor', 'MagicResist'],
        'assassin': ['AdaptiveForcePlus', 'AdaptiveForce', 'Armor'],
        'support': ['AdaptiveForce', 'Armor', 'HealthScaling'],
        'jungle': ['AttackSpeed', 'AdaptiveForce', 'Armor'],
    }

    # 角色中文名称
    ROLE_NAMES = {
        'mage': '法师',
        'marksman': '射手',
        'fighter': '战士',
        'tank': '坦克',
        'assassin': '刺客',
        'support': '辅助',
        'jungle': '打野',
    }

    def __init__(self):
        pass

    def generate_runes(self, roles: List[str], damage_type: str = '') -> Dict[str, Any]:
        """
        根据角色定位生成符文推荐

        Args:
            roles: 角色定位列表，如 ['mage', 'support']
            damage_type: 伤害类型，如 'magic', 'physical', 'mixed'

        Returns:
            符文推荐数据
        """
        if not roles:
            roles = ['fighter']

        # 确定主要角色
        primary_role = roles[0]
        secondary_role = roles[1] if len(roles) > 1 else None

        # 获取基石符文和主系树
        keystone_info = self.KEYSTONE_MAP.get(primary_role, ('Precision', ['Conqueror']))
        primary_tree = keystone_info[0]
        keystones = keystone_info[1]

        # 获取副系树
        secondary_tree = self.SECONDARY_PAIRINGS.get(primary_tree, ['Domination'])[0]
        if secondary_role:
            # 如果副系角色对应不同的树，可以调整
            alt_tree = self.KEYSTONE_MAP.get(secondary_role, (None, []))[0]
            if alt_tree and alt_tree != primary_tree:
                secondary_tree = alt_tree

        # 构建符文数据
        result = {
            'primary_tree': primary_tree,
            'primary_tree_id': self.RUNE_TREE_IDS.get(primary_tree),
            'keystone': keystones[0],
            'primary_runes': self._get_primary_runes(primary_tree, damage_type),
            'secondary_tree': secondary_tree,
            'secondary_tree_id': self.RUNE_TREE_IDS.get(secondary_tree),
            'secondary_runes': self._get_secondary_runes(secondary_tree, damage_type),
            'shards': self.SHARD_MAP.get(primary_role, ['AdaptiveForcePlus', 'AdaptiveForce', 'Armor']),
            'shard_ids': [],
        }
        result['shard_ids'] = [self.SHARD_MAPPING.get(s, 5005) for s in result['shards']]

        return result

    def _get_primary_runes(self, tree: str, damage_type: str) -> List[str]:
        """获取主系符文（除基石外的 3 个）"""
        runes = self.PRIMARY_RUNES.get(tree, self.PRIMARY_RUNES['Precision'])
        return runes[:3]

    def _get_secondary_runes(self, tree: str, damage_type: str) -> List[str]:
        """获取副系符文（2 个）"""
        runes = self.PRIMARY_RUNES.get(tree, self.PRIMARY_RUNES['Precision'])
        return runes[:2]

    def format_for_db(self, result: Dict[str, Any]) -> Dict[str, Optional[str]]:
        """格式化符文数据为数据库 JSON 格式"""
        if not result:
            return {'primary_runes': None, 'secondary_runes': None, 'shards': None}

        # 主系符文
        primary_data = {
            'tree': result['primary_tree'],
            'tree_id': result['primary_tree_id'],
            'keystone': result.get('keystone'),
            'runes': result['primary_runes']
        }

        # 副系符文
        secondary_data = {
            'tree': result['secondary_tree'],
            'tree_id': result['secondary_tree_id'],
            'runes': result['secondary_runes']
        }

        # 符文碎片
        shards_data = {
            'shards': result.get('shards', [])
        }

        return {
            'primary_runes': json.dumps(primary_data, ensure_ascii=False),
            'secondary_runes': json.dumps(secondary_data, ensure_ascii=False),
            'shards': json.dumps(shards_data, ensure_ascii=False),
        }


# 测试
if __name__ == '__main__':
    generator = RuneGenerator()

    test_cases = [
        (['mage'], 'magic', '黑暗之女'),
        (['fighter', 'assassin'], 'physical', '疾风剑豪'),
        (['marksman'], 'physical', '暗夜猎手'),
        (['mage', 'support'], 'magic', '九尾妖狐'),
        (['tank', 'fighter'], 'physical', '熔岩巨兽'),
    ]

    for roles, damage_type, hero_name in test_cases:
        print(f"\n{'='*60}")
        print(f"{hero_name} - Roles: {roles}, Damage: {damage_type}")
        print('='*60)

        result = generator.generate_runes(roles, damage_type)
        print(f"  主系：{result['primary_tree']} - {result['keystone']}")
        print(f"  主系符文：{result['primary_runes']}")
        print(f"  副系：{result['secondary_tree']}")
        print(f"  副系符文：{result['secondary_runes']}")
        print(f"  碎片：{result['shards']}")

        # 数据库格式
        db_format = generator.format_for_db(result)
        print(f"\n  数据库格式:")
        print(f"    primary_runes: {db_format['primary_runes'][:80]}...")
