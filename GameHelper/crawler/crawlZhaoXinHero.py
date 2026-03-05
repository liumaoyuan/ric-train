#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
英雄联盟赵信英雄数据爬虫
爬取赵信（heroid=5）数据并存储到数据库，与 game_entity 表关联
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

import requests


class LOLZhaoXinCrawler:
    """英雄联盟赵信英雄数据爬虫"""

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
        """解析英雄数据为详情表格式"""
        hero = hero_data.get('hero', {})
        skins = hero_data.get('skins', [])
        spells = hero_data.get('spells', [])

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
            'skill_order': self._generate_skill_order(spells),
            'skill_max_order': self._suggest_skill_max_order(spells),

            # 对线技巧
            'ally_tips': hero.get('allytips', []),
            'enemy_tips': hero.get('enemytips', []),

            # 皮肤数量
            'skin_count': len(skins),

            # 出装推荐
            'starting_items': self._suggest_starting_items(hero),
            'core_items': self._suggest_core_items(hero),
            'boots_recommendation': self._suggest_boots(hero),
            'summoner_spells': self._suggest_summoner_spells(hero),
        }

        return result

    def _generate_skill_order(self, spells: List[Dict]) -> str:
        if not spells:
            return ''
        spell_keys = [s.get('spellKey', '').upper() for s in spells if s.get('spellKey')]
        if 'Q' in spell_keys:
            return 'QWEQQQ'
        return 'QWE'

    def _suggest_skill_max_order(self, spells: List[Dict]) -> str:
        if not spells:
            return ''
        for spell in spells:
            key = spell.get('spellKey', '').upper()
            if key in ['Q', 'W', 'E']:
                return f"{key}>E>W" if key == 'Q' else f"Q>{key}>W"
        return 'Q>W>E'

    def _suggest_starting_items(self, hero: Dict) -> Dict[str, Any]:
        roles = hero.get('roles', [])
        damage_type = hero.get('damageType', '')
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
        roles = hero.get('roles', [])
        damage_type = hero.get('damageType', '')
        recommendations = []
        if 'assassin' in roles or 'fighter' in roles:
            recommendations = [
                {'itemId': '3071', 'name': '黑切', 'reason': '提供血量和穿甲'},
                {'itemId': '3153', 'name': '破败王者之刃', 'reason': '提供攻击力和吸血'},
                {'itemId': '3053', 'name': '斯特拉克的挑战护手', 'reason': '提供血量和护盾'},
            ]
        elif 'mage' in roles or damage_type == 'kMagic':
            recommendations = [
                {'itemId': '3152', 'name': '海克斯科技火箭腰带', 'reason': '提供法穿和主动突进'},
                {'itemId': '3089', 'name': '帽子', 'reason': '大幅提升法术强度'},
                {'itemId': '3135', 'name': '虚空之杖', 'reason': '高法穿应对坦克'},
            ]
        else:
            recommendations = [
                {'itemId': '3071', 'name': '黑切', 'reason': '通用战士装备'},
                {'itemId': '3053', 'name': '斯特拉克的挑战护手', 'reason': '提供生存能力'},
            ]
        return {'items': recommendations, 'description': '核心装备推荐'}

    def _suggest_boots(self, hero: Dict) -> Dict[str, Any]:
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
        roles = hero.get('roles', [])
        if 'jungle' in roles or 'assassin' in roles:
            return {
                'primary': {'id': '11', 'name': '惩戒', 'reason': '打野必备'},
                'secondary': {'id': '4', 'name': '闪现', 'reason': 'Gank 和逃生'},
            }
        elif 'mage' in roles or 'marksman' in roles:
            return {
                'primary': {'id': '4', 'name': '闪现', 'reason': '必备保命技能'},
                'secondary': {'id': '7', 'name': '点燃', 'reason': '增强击杀能力'},
            }
        else:
            return {
                'primary': {'id': '4', 'name': '闪现', 'reason': '通用技能'},
                'secondary': {'id': '21', 'name': '屏障', 'reason': '增强生存'},
            }


def crawl_zhaoxin_to_database():
    """爬取赵信数据并存储到数据库"""
    from GameHelper.models.gameHeroDetailModel import GameHeroDetailModel
    from GameHelper.models.gameEntityModel import GameEntityModel
    import json

    print("\n" + "=" * 60)
    print("  爬取英雄联盟赵信数据并存储到数据库")
    print("=" * 60 + "\n")

    crawler = LOLZhaoXinCrawler()
    hero_id = "5"  # 赵信的 ID（德邦总管）

    # 获取物品数据
    crawler.fetch_items()

    # 获取赵信详情
    print(f"正在爬取赵信 (ID={hero_id}) 的数据...")
    hero_detail = crawler.fetch_hero_detail(hero_id)

    if not hero_detail:
        print(f"获取赵信数据失败")
        return

    try:
        # 解析数据
        parsed_data = crawler.parse_hero_for_detail(hero_detail)
        hero = hero_detail.get('hero', {})

        print(f"\n英雄信息:")
        print(f"  名称：{parsed_data['hero_name']}")
        print(f"  称号：{parsed_data['hero_title']}")
        print(f"  定位：{parsed_data['roles']}")
        print(f"  阵营：{parsed_data['camp']}")
        print(f"  伤害类型：{parsed_data['damage_type']}")

        # 1. 先确保 game_entity 表中有赵信记录
        print("\n正在检查/创建 game_entity 记录...")
        entity = GameEntityModel.get_by_entity_code(hero_id, "英雄联盟")

        if entity:
            print(f"  ✓ 已找到 game_entity 记录：ID={entity.id}")
        else:
            entity = GameEntityModel(
                entity_name=parsed_data['hero_name'],
                entity_code=hero_id,
                entity_type="hero",
                game_name="英雄联盟",
                aliases=parsed_data.get('hero_alias', ''),
                description=f"{parsed_data['hero_title']} - {parsed_data['roles']}",
                status=1
            )
            entity.save()
            print(f"  ✓ 已创建 game_entity 记录：ID={entity.id}")

        # 2. 检查是否已存在详情记录
        print("\n正在检查 game_hero_detail 记录...")
        existing = GameHeroDetailModel.get_by_hero_id(hero_id, "英雄联盟")

        # 将 dict 和 list 转换为 JSON 字符串
        starting_items_json = json.dumps(parsed_data.get('starting_items'), ensure_ascii=False) if parsed_data.get('starting_items') else None
        core_items_json = json.dumps(parsed_data.get('core_items'), ensure_ascii=False) if parsed_data.get('core_items') else None
        boots_recommendation_json = json.dumps(parsed_data.get('boots_recommendation'), ensure_ascii=False) if parsed_data.get('boots_recommendation') else None
        summoner_spells_json = json.dumps(parsed_data.get('summoner_spells'), ensure_ascii=False) if parsed_data.get('summoner_spells') else None
        ally_tips_json = json.dumps(parsed_data.get('ally_tips'), ensure_ascii=False) if parsed_data.get('ally_tips') else None
        enemy_tips_json = json.dumps(parsed_data.get('enemy_tips'), ensure_ascii=False) if parsed_data.get('enemy_tips') else None

        if existing:
            print(f"  ! 赵信详情记录已存在，进行更新...")
            existing.hero_alias = parsed_data.get('hero_alias')
            existing.hero_title = parsed_data.get('hero_title')
            existing.roles = parsed_data.get('roles')
            existing.camp = parsed_data.get('camp')
            existing.damage_type = parsed_data.get('damage_type')
            existing.hp = parsed_data.get('hp')
            existing.hp_per_level = parsed_data.get('hp_per_level')
            existing.mp = parsed_data.get('mp')
            existing.mp_per_level = parsed_data.get('mp_per_level')
            existing.attack_damage = parsed_data.get('attack_damage')
            existing.attack_damage_per_level = parsed_data.get('attack_damage_per_level')
            existing.attack_speed = parsed_data.get('attack_speed')
            existing.attack_speed_per_level = parsed_data.get('attack_speed_per_level')
            existing.armor = parsed_data.get('armor')
            existing.armor_per_level = parsed_data.get('armor_per_level')
            existing.magic_resist = parsed_data.get('magic_resist')
            existing.magic_resist_per_level = parsed_data.get('magic_resist_per_level')
            existing.move_speed = parsed_data.get('move_speed')
            existing.attack_range = parsed_data.get('attack_range')
            existing.hp_regen = parsed_data.get('hp_regen')
            existing.mp_regen = parsed_data.get('mp_regen')
            existing.attack_rating = parsed_data.get('attack_rating')
            existing.defense_rating = parsed_data.get('defense_rating')
            existing.magic_rating = parsed_data.get('magic_rating')
            existing.difficulty_rating = parsed_data.get('difficulty_rating')
            existing.mobility_rating = parsed_data.get('mobility_rating')
            existing.utility_rating = parsed_data.get('utility_rating')
            existing.crowd_control_rating = parsed_data.get('crowd_control_rating')
            existing.skill_order = parsed_data.get('skill_order')
            existing.skill_max_order = parsed_data.get('skill_max_order')
            existing.starting_items = starting_items_json
            existing.core_items = core_items_json
            existing.boots_recommendation = boots_recommendation_json
            existing.summoner_spells = summoner_spells_json
            existing.ally_tips = ally_tips_json
            existing.enemy_tips = enemy_tips_json
            existing.skin_count = parsed_data.get('skin_count', 0)
            existing.save()
            print(f"  ✓ 已更新 game_hero_detail 记录")
        else:
            print(f"  创建新的 game_hero_detail 记录...")
            # 创建新的详情记录
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
                starting_items=starting_items_json,
                core_items=core_items_json,
                boots_recommendation=boots_recommendation_json,
                summoner_spells=summoner_spells_json,
                ally_tips=ally_tips_json,
                enemy_tips=enemy_tips_json,
                skin_count=parsed_data.get('skin_count', 0),
                status=1,
            )
            print(f"  准备保存数据...")
            detail.save()
            print(f"  ✓ 已创建 game_hero_detail 记录")

        print("\n" + "=" * 60)
        print("  赵信数据爬取完成")
        print("=" * 60 + "\n")

        # 显示技能信息
        spells = hero_detail.get('spells', [])
        if spells:
            print("\n赵信技能:")
            for spell in spells:
                print(f"  {spell.get('spellKey', '').upper()}: {spell.get('name', 'Unknown')}")

    except Exception as e:
        print(f"\n✗ 保存数据失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    crawl_zhaoxin_to_database()
