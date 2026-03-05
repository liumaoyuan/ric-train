#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
英雄联盟英雄详情爬虫
爬取英雄详细信息并存储到数据库
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
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

import requests


class LOLHeroDetailCrawler:
    """英雄联盟英雄详情爬虫"""

    HERO_LIST_API = "https://game.gtimg.cn/images/lol/act/img/js/heroList/hero_list.js"
    HERO_DETAIL_API = "https://game.gtimg.cn/images/lol/act/img/js/hero/{hero_id}.js"
    ITEM_LIST_API = "https://game.gtimg.cn/images/lol/act/img/js/items/items.js"

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://lol.qq.com/',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.items_cache = {}

    def fetch_items(self) -> Dict[str, Any]:
        """获取物品列表"""
        logger.info("正在获取物品列表...")
        try:
            response = self.session.get(self.ITEM_LIST_API, timeout=30)
            response.raise_for_status()
            data = response.json()
            self.items_cache = {item['itemId']: item for item in data.get('items', [])}
            logger.info(f"成功获取 {len(self.items_cache)} 个物品")
            return data
        except Exception as e:
            logger.error(f"获取物品列表失败：{e}")
            return {}

    def fetch_hero_list(self) -> List[Dict[str, Any]]:
        """获取英雄列表"""
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
        """获取英雄详情"""
        api_url = self.HERO_DETAIL_API.format(hero_id=hero_id)
        try:
            response = self.session.get(api_url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取英雄详情失败 (ID={hero_id}): {e}")
            return None

    def parse_hero_for_detail(self, hero_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析英雄数据为详情表格式

        Args:
            hero_data: 英雄原始数据

        Returns:
            详情表格式的数据
        """
        hero = hero_data.get('hero', {})
        skins = hero_data.get('skins', [])
        spells = hero_data.get('spells', [])

        # 解析属性数据
        def parse_float(value, default=None):
            try:
                return float(value) if value else default
            except:
                return default

        def parse_int(value, default=None):
            try:
                return int(value) if value else default
            except:
                return default

        # 提取基本信息
        result = {
            'hero_id': hero.get('heroId', ''),
            'hero_name': hero.get('name', ''),
            'hero_alias': hero.get('alias', ''),
            'hero_title': hero.get('title', ''),
            'roles': ','.join(hero.get('roles', [])) if hero.get('roles') else '',
            'camp': hero.get('camp', ''),
            'damage_type': hero.get('damageType', ''),

            # 基础属性
            'hp': parse_float(hero.get('hp')),
            'hp_per_level': parse_float(hero.get('hpperlevel')),
            'mp': parse_float(hero.get('mp')),
            'mp_per_level': parse_float(hero.get('mpperlevel')),
            'attack_damage': parse_float(hero.get('attackdamage')),
            'attack_damage_per_level': parse_float(hero.get('attackdamageperlevel')),
            'attack_speed': parse_float(hero.get('attackspeed')),
            'attack_speed_per_level': parse_float(hero.get('attackspeedperlevel')),
            'armor': parse_float(hero.get('armor')),
            'armor_per_level': parse_float(hero.get('armorperlevel')),
            'magic_resist': parse_float(hero.get('spellblock')),
            'magic_resist_per_level': parse_float(hero.get('spellblockperlevel')),
            'move_speed': parse_int(hero.get('movespeed')),
            'attack_range': parse_int(hero.get('attackrange')),
            'hp_regen': parse_float(hero.get('hpregen')),
            'mp_regen': parse_float(hero.get('mpregen')),

            # 英雄评分
            'attack_rating': parse_int(hero.get('attack')),
            'defense_rating': parse_int(hero.get('defense')),
            'magic_rating': parse_int(hero.get('magic')),
            'difficulty_rating': parse_int(hero.get('difficulty')),
            'mobility_rating': parse_int(hero.get('mobility')),
            'utility_rating': parse_int(hero.get('utility')),
            'crowd_control_rating': parse_int(hero.get('crowdControl')),

            # 技能数据
            'spells': spells,

            # 技能加点推荐 (根据技能顺序生成)
            'skill_order': self._generate_skill_order(spells),
            'skill_max_order': self._suggest_skill_max_order(spells),

            # 对线技巧
            'ally_tips': hero.get('allytips', []),
            'enemy_tips': hero.get('enemytips', []),

            # 皮肤数量
            'skin_count': len(skins),

            # 出装推荐 (基于英雄角色和伤害类型生成)
            'starting_items': self._suggest_starting_items(hero),
            'core_items': self._suggest_core_items(hero),
            'boots_recommendation': self._suggest_boots(hero),

            # 召唤师技能推荐
            'summoner_spells': self._suggest_summoner_spells(hero),
        }

        return result

    def _generate_skill_order(self, spells: List[Dict]) -> str:
        """生成技能加点顺序"""
        if not spells:
            return ''

        # 根据技能数据生成加点建议
        # 这里简化处理，实际应该根据技能升级收益来计算
        spell_keys = [s.get('spellKey', '').upper() for s in spells if s.get('spellKey')]

        # 默认加点顺序 (需要根据具体英雄调整)
        if 'Q' in spell_keys:
            return 'QWEQQQ'
        return 'QWE'

    def _suggest_skill_max_order(self, spells: List[Dict]) -> str:
        """建议主副技能加点"""
        if not spells:
            return ''

        # 根据技能类型判断
        for spell in spells:
            key = spell.get('spellKey', '').upper()
            name = spell.get('name', '')

            # 通常主升清兵或消耗技能
            if key in ['Q', 'W', 'E']:
                return f"{key}>E>W" if key == 'Q' else f"Q>{key}>W"

        return 'Q>W>E'

    def _suggest_starting_items(self, hero: Dict) -> Dict[str, Any]:
        """根据英雄类型建议出门装"""
        roles = hero.get('roles', [])
        damage_type = hero.get('damageType', '')

        # 基于角色和伤害类型的简单推荐逻辑
        recommendations = []

        if 'mage' in roles or damage_type == 'kMagic':
            recommendations = [
                {'itemId': '1056', 'name': '多兰之戒', 'reason': '提供法术强度和法力回复'},
                {'itemId': '2003', 'name': '生命药水', 'count': 2},
            ]
        elif 'marksman' in roles:
            recommendations = [
                {'itemId': '1055', 'name': '多兰之刃', 'reason': '提供攻击力和生命偷取'},
                {'itemId': '2003', 'name': '生命药水', 'count': 1},
            ]
        elif 'tank' in roles or 'fighter' in roles:
            recommendations = [
                {'itemId': '1054', 'name': '多兰之盾', 'reason': '提供生命值和生命回复'},
                {'itemId': '2003', 'name': '生命药水', 'count': 1},
            ]
        else:
            recommendations = [
                {'itemId': '1054', 'name': '多兰之盾', 'reason': '通用出门装'},
                {'itemId': '2003', 'name': '生命药水', 'count': 1},
            ]

        return {'items': recommendations, 'description': '推荐出门装'}

    def _suggest_core_items(self, hero: Dict) -> Dict[str, Any]:
        """根据英雄类型建议核心装备"""
        roles = hero.get('roles', [])
        damage_type = hero.get('damageType', '')

        # 基于角色的装备推荐
        recommendations = []

        if 'mage' in roles or damage_type == 'kMagic':
            recommendations = [
                {'itemId': '3152', 'name': '海克斯科技火箭腰带', 'reason': '提供法穿和主动突进'},
                {'itemId': '3089', 'name': '帽子', 'reason': '大幅提升法术强度'},
                {'itemId': '3135', 'name': '虚空之杖', 'reason': '高法穿应对坦克'},
            ]
        elif 'marksman' in roles:
            recommendations = [
                {'itemId': '3031', 'name': '无尽之刃', 'reason': '提供暴击和攻击力'},
                {'itemId': '3094', 'name': '疾射火炮', 'reason': '增加攻击距离'},
                {'itemId': '3036', 'name': '多米尼克领主的致意', 'reason': '百分比穿甲'},
            ]
        elif 'assassin' in roles:
            recommendations = [
                {'itemId': '3142', 'name': '幽梦之灵', 'reason': '提供穿甲和移速'},
                {'itemId': '3814', 'name': '夜之锋刃', 'reason': '保命和穿甲'},
                {'itemId': '3179', 'name': '亵渎九头蛇', 'reason': '提供清线和爆发'},
            ]
        elif 'tank' in roles:
            recommendations = [
                {'itemId': '3068', 'name': '日炎圣盾', 'reason': '提供坦度和清线'},
                {'itemId': '3742', 'name': '死舞', 'reason': '提供护甲和减伤'},
                {'itemId': '3065', 'name': '精神_VIS 力', 'reason': '提供魔抗和回复'},
            ]
        elif 'fighter' in roles:
            recommendations = [
                {'itemId': '3071', 'name': '黑切', 'reason': '提供血量和穿甲'},
                {'itemId': '3053', 'name': '斯特拉克的挑战护手', 'reason': '提供血量和护盾'},
                {'itemId': '3748', 'name': '泰坦', 'reason': '提供血量和伤害'},
            ]
        else:
            recommendations = [
                {'itemId': '3071', 'name': '黑切', 'reason': '通用战士装备'},
                {'itemId': '3053', 'name': '斯特拉克的挑战护手', 'reason': '提供生存能力'},
            ]

        return {'items': recommendations, 'description': '核心装备推荐'}

    def _suggest_boots(self, hero: Dict) -> Dict[str, Any]:
        """建议鞋子"""
        damage_type = hero.get('damageType', '')
        roles = hero.get('roles', [])

        if 'mage' in roles or damage_type == 'kMagic':
            return {'itemId': '3020', 'name': '法师之靴', 'reason': '提供法术穿透'}
        elif 'marksman' in roles:
            return {'itemId': '3006', 'name': '狂战士胫甲', 'reason': '提供攻击速度'}
        elif 'tank' in roles:
            return {'itemId': '3047', 'name': '铁板靴', 'reason': '提供护甲和减伤'}
        else:
            return {'itemId': '3111', 'name': '水银之靴', 'reason': '提供韧性和魔抗'}

    def _suggest_summoner_spells(self, hero: Dict) -> Dict[str, Any]:
        """建议召唤师技能"""
        roles = hero.get('roles', [])

        # 基于位置的推荐
        if 'mage' in roles or 'marksman' in roles:
            return {
                'primary': {'id': '4', 'name': '闪现', 'reason': '必备保命技能'},
                'secondary': {'id': '7', 'name': '点燃', 'reason': '增强击杀能力'},
            }
        elif 'jungle' in roles or 'assassin' in roles:
            return {
                'primary': {'id': '11', 'name': '惩戒', 'reason': '打野必备'},
                'secondary': {'id': '4', 'name': '闪现', 'reason': 'Gank 和逃生'},
            }
        elif 'tank' in roles:
            return {
                'primary': {'id': '4', 'name': '闪现', 'reason': '开团必备'},
                'secondary': {'id': '14', 'name': '引燃', 'reason': '增强击杀'},
            }
        else:
            return {
                'primary': {'id': '4', 'name': '闪现', 'reason': '通用技能'},
                'secondary': {'id': '21', 'name': '屏障', 'reason': '增强生存'},
            }


def crawl_hero_detail_to_database():
    """爬取英雄详情并存储到数据库"""
    from GameHelper.crawler.lolHeroCrawler import LOLHeroCrawler
    from GameHelper.models.gameHeroDetailModel import GameHeroDetailModel
    from GameHelper.models.gameEntityModel import GameEntityModel

    print("\n" + "=" * 60)
    print("  爬取英雄联盟英雄详情并存储到数据库")
    print("=" * 60 + "\n")

    crawler = LOLHeroDetailCrawler()

    # 获取物品数据
    crawler.fetch_items()

    # 获取英雄列表
    heroes = crawler.fetch_hero_list()
    if not heroes:
        print("获取英雄列表失败")
        return

    saved_count = 0
    skip_count = 0
    error_count = 0

    print(f"开始爬取 {len(heroes)} 个英雄详情...\n")

    for hero in heroes:
        hero_name = hero.get('name', '')
        hero_id = str(hero.get('heroId', ''))

        # 检查是否已存在 - 使用默认数据库连接
        db = GameHeroDetailModel.get_db_connection()
        if db:
            table_name = 'game_hero_detail'
            existing = db.execute(f"SELECT id FROM {table_name} WHERE hero_id = %s AND game_name = %s LIMIT 1", (hero_id, '英雄联盟'))
            if existing:
                skip_count += 1
                continue

        # 获取英雄详情
        hero_detail = crawler.fetch_hero_detail(hero_id)

        if hero_detail:
            try:
                # 解析数据
                parsed_data = crawler.parse_hero_for_detail(hero_detail)

                # 创建英雄详情记录 - 使用默认数据库连接
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
                    starting_items=parsed_data.get('starting_items'),
                    core_items=parsed_data.get('core_items'),
                    boots_recommendation=parsed_data.get('boots_recommendation'),
                    summoner_spells=parsed_data.get('summoner_spells'),
                    ally_tips=parsed_data.get('ally_tips'),
                    enemy_tips=parsed_data.get('enemy_tips'),
                    skin_count=parsed_data.get('skin_count', 0),
                    status=1,
                )
                # 使用默认数据库连接保存
                detail.save()
                saved_count += 1
                print(f"  ✓ 已保存：{hero_name} - {parsed_data.get('roles', 'Unknown')}")

            except Exception as e:
                error_count += 1
                print(f"  ✗ 保存失败 ({hero_name}): {e}")
        else:
            error_count += 1

        # 避免请求过快
        time.sleep(0.05)

    print(f"\n爬取完成:")
    print(f"  新保存：{saved_count} 个英雄")
    print(f"  已跳过：{skip_count} 个英雄")
    print(f"  失败：{error_count} 个英雄")


if __name__ == '__main__':
    crawl_hero_detail_to_database()
