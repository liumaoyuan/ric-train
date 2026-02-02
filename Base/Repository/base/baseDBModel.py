import logging
from typing import Optional, Dict, Any, List, Type, TypeVar, ClassVar
from abc import ABC, abstractproperty
from pydantic import BaseModel, Field, ConfigDict

from Base.Repository.base.baseConnection import BaseConnection

logger = logging.getLogger(__name__)
T = TypeVar('T', bound='BaseDBModel')


class BaseDBModel(BaseModel, ABC):
    """
    数据库模型基类，继承自 Pydantic BaseModel 和 ABC
    
    子类需要定义：
    - table_alias (ClassVar[str]): 表别名（可选），默认使用类名小写作为表名
    - id (Optional[int]): 主键字段（基类已定义，子类可覆盖以自定义类型或描述）
    
    支持多数据源/多数据库：
    1. 设置默认连接：BaseDBModel.set_default_db_connection()
    2. 为实例设置连接：model.set_connection()
    3. 为类设置连接：MyModel.set_db_connection()
    
    使用示例：
        # 初始化默认连接
        BaseDBModel.set_default_db_connection(default_db)
        
        # 为特定类设置连接
        User.set_db_connection(user_db)
        Order.set_db_connection(order_db)
        
        # 为实例设置连接（支持读写分离）
        user = User.get_by_id(1)
        user.set_connection(write_db)
        user.update(name="李四")
        
        # 插入
        user = User(name="张三", email="zhangsan@example.com")
        user_id = user.save()
        
        # 查询（使用类的默认连接）
        user = User.get_by_id(1)
        
        # 更新（使用实例的特定连接）
        user.name = "李四"
        user.update()
        
        # 删除
        user.delete()
    """
    
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True
    )
    
    # 类变量：表名别名（可选）
    table_alias: ClassVar[Optional[str]] = None
    # 类变量：默认数据库连接（全局默认）
    _default_db_connection: ClassVar[Optional[BaseConnection]] = None
    # 类变量：每个类可以有自己的连接
    _db_connection: ClassVar[Optional[BaseConnection]] = None
    # 实例变量：实例级别的连接（优先级最高）
    _instance_db_connection: Optional[BaseConnection] = None
    
    # 抽象属性：主键字段（子类可以覆盖此属性以自定义类型或描述）
    # 注意：id 字段在基类中已定义，子类可以覆盖此字段以自定义类型或验证规则
    id: Optional[int] = Field(None, description="主键ID", exclude=True)
    
    def __init_subclass__(cls, **kwargs):
        """子类初始化时调用，用于验证子类是否满足要求"""
        super().__init_subclass__(**kwargs)
        
        # 检查子类是否包含 id 字段（继承或重新定义都可以）
        # 注意：因为基类已经定义了 id 字段，子类会自动继承
        # 这个检查主要确保子类不会意外排除 id 字段
        if 'id' not in cls.model_fields:
            raise NotImplementedError(
                f"子类 {cls.__name__} 必须包含 'id' 字段作为主键。\n"
                f"原因：id 字段可能在子类中被意外排除。\n"
                f"请在子类中定义：id: Optional[int] = Field(..., description='主键描述')\n"
                f"或者确保没有通过 model_config 或其他方式排除 id 字段。"
            )
        
        # 检查 id 字段是否被意外标记为 required（应该是 Optional）
        id_field = cls.model_fields['id']
        if not id_field.is_required():
            logger.debug(f"子类 {cls.__name__} 已通过 BaseDBModel 初始化检查，包含 id 字段")
        else:
            logger.warning(
                f"子类 {cls.__name__} 的 id 字段被标记为必填字段（is_required=True）。\n"
                f"建议：id 字段应该是 Optional[int] 类型，以便在插入新记录时可以自动生成。"
            )
    
    @classmethod
    def set_default_db_connection(cls, db_connection: BaseConnection):
        """设置全局默认数据库连接（所有模型类的默认连接）"""
        cls._default_db_connection = db_connection
        logger.debug(f"设置全局默认数据库连接")
    
    @classmethod
    def set_db_connection(cls, db_connection: BaseConnection):
        """为特定模型类设置数据库连接（覆盖默认连接）"""
        cls._db_connection = db_connection
        logger.debug(f"为 {cls.__name__} 设置数据库连接")
    
    def set_connection(self, db_connection: BaseConnection):
        """为实例设置数据库连接（支持读写分离等场景，优先级最高）"""
        self._instance_db_connection = db_connection
        logger.debug(f"为 {self.__class__.__name__} 实例设置数据库连接")
    
    def get_connection(self) -> BaseConnection:
        """获取数据库连接（优先级：实例 > 类 > 默认）"""
        # 优先级1：实例级别的连接
        if self._instance_db_connection is not None:
            return self._instance_db_connection
        # 优先级2：类级别的连接
        if self.__class__._db_connection is not None:
            return self.__class__._db_connection
        # 优先级3：全局默认连接
        if self.__class__._default_db_connection is not None:
            return self.__class__._default_db_connection
        raise RuntimeError(
            f"数据库连接未设置。请使用以下方法之一：\n"
            f"1. BaseDBModel.set_default_db_connection() - 设置全局默认连接\n"
            f"2. {self.__class__.__name__}.set_db_connection() - 为该类设置连接\n"
            f"3. model.set_connection() - 为实例设置连接"
        )
    
    @classmethod
    def get_db_connection(cls) -> BaseConnection:
        """获取数据库连接（类方法，用于类级别的操作）"""
        if cls._db_connection is not None:
            return cls._db_connection
        if cls._default_db_connection is not None:
            return cls._default_db_connection
        raise RuntimeError(
            f"数据库连接未设置。请使用以下方法之一：\n"
            f"1. BaseDBModel.set_default_db_connection() - 设置全局默认连接\n"
            f"2. {cls.__name__}.set_db_connection() - 为该类设置连接"
        )
    
    @classmethod
    def get_table_name(cls) -> str:
        """获取表名，优先使用 table_alias，否则使用类名小写"""
        if cls.table_alias:
            return cls.table_alias
        # 将类名从驼峰转换为下划线命名
        class_name = cls.__name__
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', class_name)
        table_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        return table_name
    
    @classmethod
    def table_exists(cls) -> bool:
        """检查表是否存在"""
        db = cls.get_db_connection()
        sql = """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
        """
        result = db.execute_query(sql, (db.config["database"], cls.get_table_name()))
        return len(result) > 0

    @classmethod
    def create_table(cls, table_sql: str) -> None:
        """创建表"""
        db = cls.get_db_connection()
        db.execute_update(table_sql, commit=True)
    
    @classmethod
    def get_by_id(cls: Type[T], id_val: int) -> Optional[T]:
        """根据ID查询记录"""
        db = cls.get_db_connection()
        table_name = cls.get_table_name()
        sql = f"SELECT * FROM `{table_name}` WHERE id = %s"
        result = db.execute_query(sql, (id_val,))
        
        if not result:
            return None
        
        return cls(**result[0])
    
    @classmethod
    def get_all(cls: Type[T], limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """查询所有记录"""
        db = cls.get_db_connection()
        table_name = cls.get_table_name()
        sql = f"SELECT * FROM `{table_name}`"
        
        if limit is not None:
            sql += f" LIMIT {offset}, {limit}"
        
        results = db.execute_query(sql)
        return [cls(**row) for row in results]
    
    @classmethod
    def find_by(cls: Type[T], **filters) -> List[T]:
        """根据条件查询记录"""
        if not filters:
            return cls.get_all()
        
        db = cls.get_db_connection()
        table_name = cls.get_table_name()
        
        where_clauses = []
        params = []
        for key, value in filters.items():
            where_clauses.append(f"{key} = %s")
            params.append(value)
        
        sql = f"SELECT * FROM `{table_name}` WHERE {' AND '.join(where_clauses)}"
        results = db.execute_query(sql, tuple(params))
        return [cls(**row) for row in results]
    
    @classmethod
    def find_one_by(cls: Type[T], **filters) -> Optional[T]:
        """根据条件查询单条记录"""
        results = cls.find_by(**filters)
        return results[0] if results else None
    
    def save(self) -> int:
        """保存记录（插入或更新），返回ID"""
        if self.id is None:
            return self._insert()
        else:
            self._update()
            return self.id
    
    def _insert(self) -> int:
        """插入记录，返回新插入的ID"""
        db = self.get_db_connection()
        table_name = self.get_table_name()
        
        # 获取所有字段（排除 None 值和内部字段）
        data = self.model_dump(exclude_none=True, exclude={'id'})
        
        if not data:
            raise ValueError("没有可插入的数据")
        
        keys = list(data.keys())
        placeholders = ",".join(["%s"] * len(keys))
        sql = f"INSERT INTO `{table_name}` ({','.join(keys)}) VALUES ({placeholders})"
        
        self.id = db.execute_insert(sql, tuple(data[k] for k in keys))
        return self.id
    
    def _update(self) -> bool:
        """更新记录，返回是否成功"""
        db = self.get_db_connection()
        table_name = self.get_table_name()
        
        # 获取所有字段（排除 None 值和内部字段）
        data = self.model_dump(exclude_none=True, exclude={'id'})
        
        if not data:
            return True
        
        sets = ",".join([f"{k}=%s" for k in data])
        sql = f"UPDATE `{table_name}` SET {sets} WHERE id = %s"
        
        affected = db.execute_update(sql, tuple(data.values()) + (self.id,))
        return affected > 0
    
    def update(self, **fields) -> bool:
        """更新指定字段"""
        for key, value in fields.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self._update()
    
    def delete(self) -> bool:
        """删除记录，返回是否成功"""
        if self.id is None:
            raise ValueError("无法删除未保存的记录")
        
        db = self.get_db_connection()
        table_name = self.get_table_name()
        sql = f"DELETE FROM `{table_name}` WHERE id = %s"
        
        affected = db.execute_update(sql, (self.id,))
        return affected > 0
    
    @classmethod
    def delete_by_id(cls, id_val: int) -> bool:
        """根据ID删除记录"""
        db = cls.get_db_connection()
        table_name = cls.get_table_name()
        sql = f"DELETE FROM `{table_name}` WHERE id = %s"
        
        affected = db.execute_update(sql, (id_val,))
        return affected > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.model_dump()
    
    @classmethod
    def count(cls) -> int:
        """查询记录总数"""
        db = cls.get_db_connection()
        table_name = cls.get_table_name()
        sql = f"SELECT COUNT(*) as count FROM `{table_name}`"
        result = db.execute_query(sql)
        return result[0]['count'] if result else 0
