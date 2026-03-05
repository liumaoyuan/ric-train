import logging
from typing import Optional, List, Dict, Any

from GameHelper.models.gameStrategyModel import GameStrategyModel
from GameHelper.models.gameEntityModel import GameEntityModel
from GameHelper.models.gameStrategyEntityRelModel import GameStrategyEntityRelModel
from GameHelper.VdbModels.VdbGameStrategy import VDBGameStrategy
from GameHelper.models.pojo.gameStrategyPo import GameStrategyPO, GameStrategyCreateRequest, GameStrategyUpdateRequest

logger = logging.getLogger(__name__)


class GameStrategyService:
    """
    游戏攻略业务逻辑层
    提供攻略的增删改查方法
    """

    @staticmethod
    def create_strategy(request: GameStrategyCreateRequest, created_by: Optional[int] = None) -> Optional[GameStrategyModel]:
        """
        创建攻略

        流程：
        1. 插入 game_strategy 表
        2. 自动提取/关联实体到 game_entity 表
        3. 插入关联关系到 game_strategy_entity_rel 表
        4. 同步插入向量数据到 VDBGameStrategy

        Args:
            request: 攻略创建请求
            created_by: 创建人 ID

        Returns:
            创建的攻略记录
        """
        try:
            # 1. 插入攻略主表
            strategy = GameStrategyModel(
                title=request.title,
                content=request.content,
                source_url=request.source_url,
                game_name=request.game_name,
                strategy_type=request.strategy_type,
                status=1,
                created_by=created_by
            )
            strategy.save()
            logger.info(f"攻略主表插入成功，ID: {strategy.id}")

            # 2. 处理实体关联
            entity_ids = []
            entity_names = []
            if request.entity_names:
                for entity_name in request.entity_names:
                    # 查找或创建实体
                    entity = GameEntityService.get_or_create_entity(
                        entity_name=entity_name,
                        game_name=request.game_name,
                        entity_type="hero"  # 默认类型，可根据需要调整
                    )
                    if entity:
                        entity_ids.append(entity.id)
                        entity_names.append(entity.entity_name)

            # 3. 插入关联关系
            if entity_ids:
                for entity_id in entity_ids:
                    rel = GameStrategyEntityRelModel(
                        strategy_id=strategy.id,
                        entity_id=entity_id,
                        relevance_score=100,
                        created_by=created_by
                    )
                    rel.save()
                logger.info(f"插入 {len(entity_ids)} 条关联关系")

            # 4. 同步到 VDB
            try:
                from Base.Ai.llms.qwenLlm import get_default_qwen_llm
                llm = get_default_qwen_llm()
                embedding_result = llm.embedding(request.title, dimensions=1024)
                # embedding 返回的是 List[List[float]]，需要取第一个元素
                embedding = embedding_result[0] if embedding_result else []

                vdb_strategy = VDBGameStrategy(
                    db_id=str(strategy.id),
                    title=request.title,
                    content=request.content or '',
                    game_name=request.game_name,
                    strategy_type=request.strategy_type,
                    entity_names=','.join(entity_names) if entity_names else '',
                    embedding=embedding
                )
                save_result = vdb_strategy.save()
                logger.info(f"VDB 同步成功，insert_count: {save_result.get('insert_count', 0)}")
            except Exception as e:
                logger.error(f"VDB 同步失败：{e}")

            return strategy

        except Exception as e:
            logger.error(f"创建攻略失败：{e}")
            return None

    @staticmethod
    def update_strategy(strategy_id: int, request: GameStrategyUpdateRequest, updated_by: Optional[int] = None) -> bool:
        """
        更新攻略

        Args:
            strategy_id: 攻略 ID
            request: 攻略更新请求
            updated_by: 更新人 ID

        Returns:
            True-成功，False-失败
        """
        try:
            strategy = GameStrategyModel.get_by_id(strategy_id)
            if not strategy:
                logger.error(f"攻略不存在，ID: {strategy_id}")
                return False

            # 更新字段
            if request.title is not None:
                strategy.title = request.title
            if request.content is not None:
                strategy.content = request.content
            if request.source_url is not None:
                strategy.source_url = request.source_url
            if request.strategy_type is not None:
                strategy.strategy_type = request.strategy_type
            if request.status is not None:
                strategy.status = request.status
            strategy.updated_by = updated_by

            strategy.save()
            logger.info(f"攻略更新成功，ID: {strategy_id}")

            # 如果更新了实体关联，需要同步更新 VDB
            if request.entity_names is not None:
                # 删除旧关联
                GameStrategyEntityRelModel.delete_by_strategy_id(strategy_id)
                # 插入新关联
                for entity_name in request.entity_names:
                    entity = GameEntityService.get_or_create_entity(
                        entity_name=entity_name,
                        game_name=strategy.game_name,
                        entity_type="hero"
                    )
                    if entity:
                        rel = GameStrategyEntityRelModel(
                            strategy_id=strategy_id,
                            entity_id=entity.id,
                            relevance_score=100
                        )
                        rel.save()

            return True

        except Exception as e:
            logger.error(f"更新攻略失败：{e}")
            return False

    @staticmethod
    def delete_strategy(strategy_id: int) -> bool:
        """
        删除攻略（软删除）

        Args:
            strategy_id: 攻略 ID

        Returns:
            True-成功，False-失败
        """
        try:
            strategy = GameStrategyModel.get_by_id(strategy_id)
            if not strategy:
                logger.error(f"攻略不存在，ID: {strategy_id}")
                return False

            strategy.status = 0
            strategy.save()
            logger.info(f"攻略软删除成功，ID: {strategy_id}")
            return True

        except Exception as e:
            logger.error(f"删除攻略失败：{e}")
            return False

    @staticmethod
    def get_strategy_by_id(strategy_id: int) -> Optional[GameStrategyPO]:
        """
        根据 ID 获取攻略详情

        Args:
            strategy_id: 攻略 ID

        Returns:
            攻略数据对象
        """
        strategy = GameStrategyModel.get_by_id(strategy_id)
        if not strategy:
            return None

        # 获取关联的实体名称
        entity_ids = GameStrategyEntityRelModel.get_entity_ids_by_strategy_id(strategy_id)
        entities = []
        for entity_id in entity_ids:
            entity = GameEntityModel.get_by_id(entity_id)
            if entity:
                entities.append(entity.entity_name)

        return GameStrategyPO(
            id=strategy.id,
            title=strategy.title,
            content=strategy.content,
            source_url=strategy.source_url,
            game_name=strategy.game_name,
            strategy_type=strategy.strategy_type,
            status=strategy.status,
            entity_names=entities
        )

    @staticmethod
    def get_strategies_by_game(game_name: str, limit: int = 100) -> List[GameStrategyPO]:
        """
        根据游戏名称获取攻略列表

        Args:
            game_name: 游戏名称
            limit: 返回数量限制

        Returns:
            攻略数据对象列表
        """
        strategies = GameStrategyModel.get_by_game_name(game_name, limit=limit)
        return [GameStrategyPO(
            id=s.id,
            title=s.title,
            content=s.content,
            source_url=s.source_url,
            game_name=s.game_name,
            strategy_type=s.strategy_type,
            status=s.status
        ) for s in strategies]

    @staticmethod
    def search_strategies(keyword: str, game_name: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        搜索攻略（使用 VDB 混合搜索）

        Args:
            keyword: 搜索关键词
            game_name: 游戏名称（可选）
            limit: 返回数量限制

        Returns:
            搜索结果列表
        """
        try:
            results = VDBGameStrategy.search_by_keyword(keyword, game_name, limit)
            return results
        except Exception as e:
            logger.error(f"搜索攻略失败：{e}")
            return []

    @staticmethod
    def get_strategies_by_entity(entity_name: str, limit: int = 100) -> List[GameStrategyPO]:
        """
        根据实体名称获取攻略列表

        Args:
            entity_name: 实体名称
            limit: 返回数量限制

        Returns:
            攻略数据对象列表
        """
        try:
            # 先查找实体
            entities = GameEntityModel.search_by_name(entity_name, limit=1)
            if not entities:
                return []

            entity = entities[0]
            # 通过关联表获取攻略 ID
            strategy_ids = GameStrategyEntityRelModel.get_strategy_ids_by_entity_id(entity.id, limit)

            strategies = []
            for strategy_id in strategy_ids:
                strategy = GameStrategyModel.get_by_id(strategy_id)
                if strategy and strategy.is_active:
                    strategies.append(GameStrategyPO(
                        id=strategy.id,
                        title=strategy.title,
                        content=strategy.content,
                        source_url=strategy.source_url,
                        game_name=strategy.game_name,
                        strategy_type=strategy.strategy_type,
                        status=strategy.status
                    ))

            return strategies

        except Exception as e:
            logger.error(f"根据实体查询攻略失败：{e}")
            return []


class GameEntityService:
    """
    游戏实体业务逻辑层
    """

    @staticmethod
    def get_or_create_entity(entity_name: str, game_name: str, entity_type: str = "hero") -> Optional[GameEntityModel]:
        """
        获取或创建实体

        Args:
            entity_name: 实体名称
            game_name: 游戏名称
            entity_type: 实体类型

        Returns:
            实体记录
        """
        try:
            # 先尝试根据名称查找
            entities = GameEntityModel.get_by_entity_name(entity_name, game_name, limit=1)
            if entities:
                return entities[0]

            # 创建新实体
            entity = GameEntityModel(
                entity_name=entity_name,
                entity_code=entity_name.lower().replace(' ', '_'),
                entity_type=entity_type,
                game_name=game_name,
                status=1
            )
            entity.save()
            logger.info(f"创建新实体：{entity_name} ({game_name})")
            return entity

        except Exception as e:
            logger.error(f"获取或创建实体失败：{e}")
            return None

    @staticmethod
    def create_entity(entity_name: str, entity_code: str, entity_type: str, game_name: str,
                      aliases: Optional[str] = None, description: Optional[str] = None) -> Optional[GameEntityModel]:
        """
        创建实体

        Args:
            entity_name: 实体名称
            entity_code: 实体编码
            entity_type: 实体类型
            game_name: 游戏名称
            aliases: 别名列表
            description: 实体描述

        Returns:
            实体记录
        """
        try:
            # 检查是否已存在
            existing = GameEntityModel.get_by_entity_code(entity_code, game_name)
            if existing:
                logger.info(f"实体已存在：{entity_code}")
                return existing

            entity = GameEntityModel(
                entity_name=entity_name,
                entity_code=entity_code,
                entity_type=entity_type,
                game_name=game_name,
                aliases=aliases,
                description=description,
                status=1
            )
            entity.save()
            logger.info(f"实体创建成功：{entity_name}")
            return entity

        except Exception as e:
            logger.error(f"创建实体失败：{e}")
            return None

    @staticmethod
    def get_entity_by_name(entity_name: str, game_name: Optional[str] = None) -> Optional[GameEntityModel]:
        """
        根据名称获取实体

        Args:
            entity_name: 实体名称
            game_name: 游戏名称（可选）

        Returns:
            实体记录
        """
        entities = GameEntityModel.get_by_entity_name(entity_name, game_name, limit=1)
        return entities[0] if entities else None

    @staticmethod
    def get_entities_by_type(entity_type: str, game_name: Optional[str] = None, limit: int = 100) -> List[GameEntityModel]:
        """
        根据类型获取实体列表

        Args:
            entity_type: 实体类型
            game_name: 游戏名称（可选）
            limit: 返回数量限制

        Returns:
            实体记录列表
        """
        return GameEntityModel.get_by_type(entity_type, game_name, limit=limit)
