from datetime import datetime
from Base.Ai.base import UserMessages
from Base.Ai.llms.qwenLlm import get_default_qwen_llm
from Base.Models.BaseParamsModel import BaseParamsModel
from Base.Models.BaseKeywordModel import BaseKeywordModel
from GameHelper.models.gameStrategyModel import GameStrategyModel
from GameHelper.models.gameEntityModel import GameEntityModel
from GameHelper.models.gameStrategyEntityRelModel import GameStrategyEntityRelModel
from GameHelper.VdbModels.VdbGameStrategy import VDBGameStrategy


def init_lol_heroes():
    """
    初始化英雄联盟英雄列表
    使用 LLM 从互联网获取所有英雄联盟游戏英雄名称，以逗号分隔存储
    """
    code = 'lol_hero'
    project_type = 'GameHelper'

    # 检查数据是否已存在
    existing_param = BaseParamsModel.get_param_by_code(code, project_type)

    if existing_param is not None:
        print(f"✓ 英雄联盟英雄数据已存在:")
        print(f"  Code: {code}")
        print(f"  英雄数量：{len(existing_param.get('value', '').split(','))} 个")
        print(f"  示例：{existing_param.get('value', '')[:100]}...")
        return

    # 获取 LLM 实例
    llm = get_default_qwen_llm()

    try:
        # 使用 LLM 获取英雄联盟英雄列表
        user_prompt = """请帮我列出英雄联盟 (LOL) 游戏中所有的英雄名称。

要求：
1. 尽可能全面，包含所有可用英雄
2. 英雄名称之间用英文逗号分隔
3. 只输出英雄名称，不要编号、不要分类、不要其他说明文字
4. 使用英雄的中文官方名称
5. 确保名称准确无误

示例格式：疾风剑豪，影流之主，诺克萨斯之手，德玛西亚之力，圣锤之毅, ...

请输出所有英雄联盟英雄名称："""

        messages = [UserMessages(prompt=user_prompt)]
        response = llm.chat(messages,enable_search=True)

        # 清理响应结果
        heroes = response.strip()
        # 移除可能的多余字符
        heroes = heroes.replace('\n', ',').replace('，', ',').replace('、', ',')
        # 移除常见的前缀说明
        for prefix in ['英雄联盟英雄：', '英雄列表：', '所有英雄：', '以下是所有英雄：']:
            heroes = heroes.replace(prefix, '')
        # 移除首尾的标点符号和空格
        heroes = heroes.strip('，。、,，:： ')

        print(f"✓ 成功获取英雄联盟英雄列表:")
        print(f"  原始响应长度：{len(response)} 字符")
        print(f"  英雄列表预览：{heroes[:200]}...")

        # 保存到数据库
        params = BaseParamsModel(
            code=code,
            value=heroes,
            desc='英雄联盟 (LOL) 所有英雄名称列表',
            type=project_type,
        )
        params.save()
        print(f"✓ 保存到数据库成功!")
        print(f"  Code: {code}")
        print(f"  Type: {project_type}")

    except Exception as e:
        print(f"✗ 获取英雄列表失败，错误：{e}")
        raise


def init_lol_heroes_keywords():
    """
    初始化英雄联盟英雄关键词数据
    遍历 base_sys_params 中的 lol_hero 数据，向 base_keyword 表插入英雄的名称、外号和同义词

    数据格式示例:
    id    keyword_name    keyword_code    keyword_desc    semantic_desc    keyword_synonyms    status    type    source
    1    沙漠死神    内瑟斯    沙漠死神    1    COMMON    MANUAL    2026-02-27 22:06:48    2026-02-27 22:06:48
    2    狗头    内瑟斯    沙漠死神    1    COMMON    MANUAL    2026-02-27 22:06:48    2026-02-27 22:06:48
    """
    code = 'lol_hero'
    project_type = 'GameHelper'

    # 获取英雄列表
    heroes_param = BaseParamsModel.get_param_by_code(code, project_type)
    if heroes_param is None:
        print(f"✗ 未找到英雄数据，请先执行 init_lol_heroes()")
        return

    heroes_str = heroes_param.get('value', '')
    if not heroes_str:
        print(f"✗ 英雄数据为空")
        return

    hero_list = [h.strip() for h in heroes_str.split(',') if h.strip()]
    print(f"✓ 共获取到 {len(hero_list)} 个英雄")

    llm = get_default_qwen_llm()
    insert_count = 0
    skip_count = 0

    for hero_name in hero_list:
        try:
            # 检查英雄名称是否已存在
            existing = BaseKeywordModel.search_by_name(hero_name, limit=1)
            if existing and any(e.keyword_name == hero_name for e in existing):
                print(f"  跳过已存在：{hero_name}")
                skip_count += 1
                continue

            # 使用 LLM 获取英雄的外号和同义词
            user_prompt = f"""请告诉我英雄联盟英雄"{hero_name}"的所有外号、别名、同义词。

要求：
1. 只输出外号/别名列表，用逗号分隔
2. 不要包含英雄原名
3. 如果没有外号，返回"无"
4. 常见的玩家称呼、简称都要包含,只要最常见3个
5. 不要出现任何括号及说明解释文字

示例：卡尔玛，扇子妈

请输出"{hero_name}"的所有外号："""

            messages = [UserMessages(prompt=user_prompt)]
            response = llm.chat(messages, enable_search=True)

            # 清理响应
            nicknames = response.strip()
            if '无' in nicknames or not nicknames:
                print(f"  - {hero_name}: 无外号")
                # 只插入英雄原名
                keyword = BaseKeywordModel(
                    keyword_name=hero_name,
                    keyword_code=hero_name,
                    keyword_desc=f'英雄联盟英雄 - {hero_name}',
                    semantic_desc=hero_name,
                    keyword_synonyms=hero_name,
                    status=1,
                    type='COMMON',
                    source='AI'
                )
                keyword.save()
                insert_count += 1
                print(f"  ✓ 插入：{hero_name}")
            else:
                # 解析外号列表
                nickname_list = [n.strip() for n in nicknames.replace('，', ',').replace('、', ',').split(',') if n.strip()]
                # 移除可能的说明文字
                nickname_list = [n for n in nickname_list if len(n) < 20 and not any(x in n for x in ['以下是', '外号有', '别名有', '包括'])]

                # 插入英雄原名
                keyword = BaseKeywordModel(
                    keyword_name=hero_name,
                    keyword_code=hero_name,
                    keyword_desc=f'英雄联盟英雄 - {hero_name}',
                    semantic_desc=hero_name,
                    keyword_synonyms=hero_name,
                    status=1,
                    type='COMMON',
                    source='AI'
                )
                keyword.save()
                insert_count += 1
                print(f"  ✓ 插入：{hero_name} (外号：{','.join(nickname_list[:3])}...)")

                # 插入每个外号
                for nickname in nickname_list:
                    if not nickname or nickname == hero_name:
                        continue
                    # 检查外号是否已存在
                    existing_nick = BaseKeywordModel.search_by_name(nickname, limit=1)
                    if existing_nick:
                        continue

                    nick_keyword = BaseKeywordModel(
                        keyword_name=nickname,
                        keyword_code=hero_name,  # 使用英雄原名作为 code
                        keyword_desc=f'英雄联盟英雄 - {hero_name} 的外号',
                        semantic_desc=hero_name,
                        keyword_synonyms=hero_name,  # 同义词指向英雄原名
                        status=1,
                        type='COMMON',
                        source='AI'
                    )
                    nick_keyword.save()
                    insert_count += 1

        except Exception as e:
            print(f"  ✗ 处理 {hero_name} 失败：{e}")
            continue

    print(f"\n=== 英雄关键词初始化完成 ===")
    print(f"  新插入：{insert_count} 条")
    print(f"  跳过：{skip_count} 条")


def init_game_strategy_tables():
    """
    初始化游戏攻略数据库表结构
    执行各个模型的 create_table_sql 创建表
    """
    print("=== 游戏攻略表结构初始化开始 ===\n")

    try:
        # 创建游戏实体表
        print("正在创建 game_entity 表...")
        GameEntityModel.create_table()
        print("✓ game_entity 表创建成功")

        # 创建攻略主表
        print("正在创建 game_strategy 表...")
        GameStrategyModel.create_table()
        print("✓ game_strategy 表创建成功")

        # 创建关联表
        print("正在创建 game_strategy_entity_rel 表...")
        GameStrategyEntityRelModel.create_table()
        print("✓ game_strategy_entity_rel 表创建成功")

        # 初始化 VDB 表（首次实例化时自动创建）
        print("正在初始化 VDB game_strategy 集合...")
        VDBGameStrategy(auto_create_collection=True)
        print("✓ VDB game_strategy 集合初始化成功")

        print("\n=== 游戏攻略表结构初始化完成 ===")

    except Exception as e:
        print(f"✗ 表结构初始化失败：{e}")
        raise


def init_test_game_strategy_data():
    """
    初始化测试攻略数据
    添加示例攻略和实体数据用于测试
    """
    print("\n=== 测试攻略数据初始化开始 ===\n")

    try:
        # 1. 先创建测试实体
        print("正在创建测试实体...")

        # 杰斯实体
        jayce = GameEntityModel.get_by_entity_name("杰斯", "英雄联盟", limit=1)
        if not jayce:
            jayce = GameEntityModel(
                entity_name="杰斯",
                entity_code="jayce",
                entity_type="hero",
                game_name="英雄联盟",
                aliases="未来守护者，杰斯宝，电耗子",
                description="来自皮尔特沃夫的天才发明家，能够切换近战和远程形态",
                status=1
            )
            jayce.save()
            print(f"  ✓ 创建实体：杰斯 (ID: {jayce.id})")
        else:
            jayce = jayce[0]
            print(f"  - 实体已存在：杰斯")

        # 海克斯大乱斗实体
        hex_brawl = GameEntityModel.get_by_entity_name("海克斯大乱斗", "英雄联盟", limit=1)
        if not hex_brawl:
            hex_brawl = GameEntityModel(
                entity_name="海克斯大乱斗",
                entity_code="hexgate_brawl",
                entity_type="mode",
                game_name="英雄联盟",
                aliases="海克斯，大乱斗",
                description="英雄联盟特殊娱乐模式，通过海克斯强化获得强大能力",
                status=1
            )
            hex_brawl.save()
            print(f"  ✓ 创建实体：海克斯大乱斗 (ID: {hex_brawl.id})")
        else:
            hex_brawl = hex_brawl[0]
            print(f"  - 实体已存在：海克斯大乱斗")

        # 2. 创建测试攻略
        print("\n正在创建测试攻略...")

        test_strategies = [
            {
                "title": "海克斯大乱斗 杰斯出装推荐",
                "content": """杰斯在海克斯大乱斗中的最强出装顺序：

1. 神话装备：星蚀
   - 提供穿甲和续航能力
   - 被动斩杀效果非常适合杰斯的 Poke 玩法

2. 核心装备：
   - 幽梦之灵：增加移速和穿甲
   - 收集者：提供额外经济来源
   - 夜之锋刃：保命装，防止被开
   - 公理圆弧：大招减 CD

3. 鞋子：CD 鞋或铁板靴

海克斯强化推荐：
- 海克斯科技门刀：切坦克神器
- 海克斯闪现：增强开团能力
- 终极海克斯：大招无限放

对线技巧：
1. 保持距离，用 QE 连招消耗
2. 切换锤形态 W 快速清线
3. 6 级后有墙就跳，打一套切锤形态收割""",
                "source_url": "https://example.com/guide/1",
                "game_name": "英雄联盟",
                "strategy_type": "出装",
                "entities": ["杰斯", "海克斯大乱斗"]
            },
            {
                "title": "海克斯大乱斗杰斯玩法攻略",
                "content": """杰斯在海克斯大乱斗中的详细玩法教学：

一、技能加点
主 Q 副 E，一级 Q，二级 E，三级 Q

二、海克斯强化选择优先级
T0：海克斯科技门刀、海克斯闪现
T1：终极海克斯、海克斯 buff
T2：其他功能性海克斯

三、连招技巧
1. 基础消耗：QE→切换锤形态→W→E→切换炮形态
2. 秒杀连招：门刀 QE→闪现 A→切换锤形态 W
3. poke 连招：远程 QE→后撤→等 CD 继续

四、注意事项
1. 不要第一个上，等对面关键技能交了再输出
2. 保留 E 技能保命，不要为了消耗乱交
3. 切换形态的被动加速要好好利用
4. 没蓝量了及时回家，不要赖线""",
                "source_url": "https://example.com/guide/2",
                "game_name": "英雄联盟",
                "strategy_type": "玩法",
                "entities": ["杰斯", "海克斯大乱斗"]
            },
            {
                "title": "英雄联盟 杰斯对线技巧",
                "content": """杰斯通用对线技巧：

1. 一级学 Q 抢 2
   - 直接 QE 连招打消耗
   - 利用被动加速走 A

2. 三级强势期
   - 有双形态伤害很高
   - 找机会打一套

3. 六级质变
   - 大招 CD 短
   - 可以频繁换血

4. 连招细节
   - QE 连招要熟练
   - 切换形态接普攻
   - 锤形态 W 可以取消后摇""",
                "source_url": "https://example.com/guide/3",
                "game_name": "英雄联盟",
                "strategy_type": "英雄攻略",
                "entities": ["杰斯"]
            }
        ]

        insert_count = 0
        for strategy_data in test_strategies:
            # 检查攻略是否已存在
            existing = GameStrategyModel.search_by_title(strategy_data["title"][:20], strategy_data["game_name"], limit=1)
            if existing:
                print(f"  - 攻略已存在：{strategy_data['title']}")
                continue

            # 创建攻略
            strategy = GameStrategyModel(
                title=strategy_data["title"],
                content=strategy_data["content"],
                source_url=strategy_data["source_url"],
                game_name=strategy_data["game_name"],
                strategy_type=strategy_data["strategy_type"],
                status=1
            )
            strategy.save()
            print(f"  ✓ 创建攻略：{strategy_data['title']} (ID: {strategy.id})")

            # 创建关联关系
            for entity_name in strategy_data["entities"]:
                # 查找实体
                entities = GameEntityModel.search_by_name(entity_name, strategy_data["game_name"], limit=1)
                if entities:
                    entity = entities[0]
                    # 检查关联是否已存在
                    if not GameStrategyEntityRelModel.exists(strategy.id, entity.id):
                        rel = GameStrategyEntityRelModel(
                            strategy_id=strategy.id,
                            entity_id=entity.id,
                            relevance_score=100
                        )
                        rel.save()

            # 同步到 VDB
            try:
                llm = get_default_qwen_llm()
                embedding_result = llm.embedding(strategy_data["title"], dimensions=1024)
                # embedding 返回的是 List[List[float]]，需要取第一个元素
                embedding = embedding_result[0] if embedding_result else []

                entity_names_str = ','.join(strategy_data["entities"])
                vdb_strategy = VDBGameStrategy(
                    db_id=str(strategy.id),
                    title=strategy_data["title"],
                    content=strategy_data["content"],
                    game_name=strategy_data["game_name"],
                    strategy_type=strategy_data["strategy_type"],
                    entity_names=entity_names_str,
                    embedding=embedding
                )
                vdb_strategy.save()
                print(f"    → VDB 同步成功")
            except Exception as e:
                print(f"    ✗ VDB 同步失败：{e}")

            insert_count += 1

        print(f"\n=== 测试攻略数据初始化完成 ===")
        print(f"  新插入：{insert_count} 条攻略")

    except Exception as e:
        print(f"✗ 测试数据初始化失败：{e}")
        raise


def data_init():
    """初始化游戏助手数据库"""
    print("=== 游戏助手数据初始化开始 ===\n")
    init_lol_heroes()
    init_lol_heroes_keywords()
    init_game_strategy_tables()
    init_test_game_strategy_data()
    print("\n=== 游戏助手数据初始化完成 ===")


if __name__ == '__main__':
    data_init()
