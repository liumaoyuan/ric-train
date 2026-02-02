"""
BaseEnvSettings 使用示例
演示如何创建自定义 Settings 类并自动加载 .env 文件
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import SettingsConfigDict

from Base.Config.setting import BaseEnvSettings


# =========================
# 示例 1: 简单的 Settings 类
# =========================

class DatabaseSettings(BaseEnvSettings):
    """数据库设置示例 - 继承 BaseEnvSettings 自动加载 .env"""

    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str

    # 可以自定义 env_prefix 来区分不同模块
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        extra="ignore",  # 忽略额外的环境变量
    )


# =========================
# 示例 2: 使用 alias 映射环境变量
# =========================

class S3Settings(BaseEnvSettings):
    """S3 设置示例 - 使用 alias 映射环境变量"""

    access_key: str = Field(..., alias="S3_ACCESS_KEY")
    secret_key: str = Field(..., alias="S3_SECRET_KEY")
    bucket_name: str = Field(..., alias="S3_BUCKET")
    region: str = Field(default="us-east-1", alias="S3_REGION")

    # 不需要配置 env_file，BaseEnvSettings 会自动查找
    model_config = SettingsConfigDict(
        env_prefix="S3_",
        extra="ignore",
    )


# =========================
# 示例 3: 使用字典式访问
# =========================

class AppConfig(BaseEnvSettings):
    """应用配置示例 - 演示字典式访问"""

    app_name: str = "MyApp"
    debug: bool = False
    version: str = "1.0.0"

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        extra="ignore",
    )


# =========================
# 示例 4: 自定义验证逻辑
# =========================

class ServerSettings(BaseEnvSettings):
    """服务器设置示例 - 使用验证器"""

    host: str = "0.0.0.0"
    port: int = Field(default=8000, gt=0, lt=65536)
    workers: int = Field(default=1, gt=0)
    timeout: int = Field(default=30, gt=0)

    model_config = SettingsConfigDict(
        env_prefix="SERVER_",
        extra="ignore",
    )


# =========================
# 使用示例
# =========================

def example_usage():
    """演示各种用法"""

    print("=" * 60)
    print("BaseEnvSettings 使用示例")
    print("=" * 60)

    # 示例 1: 创建实例，自动从 .env 加载
    print("\n1. 创建 DatabaseSettings 实例:")
    db_settings = DatabaseSettings()
    print(f"   Host: {db_settings.host}")
    print(f"   Port: {db_settings.port}")
    print(f"   Database: {db_settings.database}")

    # 示例 2: 使用 get() 方法安全访问
    print("\n2. 使用 get() 方法安全访问:")
    app_config = AppConfig()
    app_name = app_config.get("app_name", "DefaultApp")
    print(f"   App Name: {app_name}")

    # 示例 3: 使用字典式访问
    print("\n3. 使用字典式访问:")
    print(f"   ['debug'] = {app_config['debug']}")
    print(f"   'version' in app_config = {'version' in app_config}")

    # 示例 4: 转换为字典
    print("\n4. 转换为字典:")
    config_dict = app_config.to_dict()
    print(f"   Keys: {list(config_dict.keys())}")

    # 示例 5: 检查字段是否存在
    print("\n5. 检查字段是否存在:")
    print(f"   'debug' in app_config = {'debug' in app_config}")
    print(f"   'nonexistent' in app_config = {'nonexistent' in app_config}")

    # 示例 6: 从自定义 .env 文件加载
    print("\n6. 从自定义 .env 文件加载:")
    from pathlib import Path
    # custom_settings = DatabaseSettings.load_env_vars(Path("./custom.env"))
    # print(f"   Loaded from custom .env: {custom_settings.database}")

    # 示例 7: 演示环境变量自动类型转换
    print("\n7. 环境变量自动类型转换:")
    print("   字符串 'true' 自动转换为 True")
    print("   字符串 '123' 自动转换为 123")
    print("   字符串 '3.14' 自动转换为 3.14")

    print("\n" + "=" * 60)
    print("✅ 所有示例运行完成！")
    print("=" * 60)


def best_practices():
    """最佳实践"""

    print("\n" + "=" * 60)
    print("最佳实践建议")
    print("=" * 60)
    print("""
1. ✅ 所有 Settings 类都继承 BaseEnvSettings
   class MySettings(BaseEnvSettings):
       field: str = "default_value"

2. ✅ 使用 env_prefix 区分不同模块
   model_config = SettingsConfigDict(
       env_prefix="MY_MODULE_",
       extra="ignore",
   )

3. ✅ 使用 Field 设置默认值和验证规则
   port: int = Field(default=3306, gt=0, lt=65536)

4. ✅ 使用 alias 映射不同的环境变量名
   api_key: str = Field(..., alias="API_KEY")

5. ✅ 使用 get() 方法安全访问
   value = settings.get("some_key", "default")

6. ✅ 使用 to_dict() 序列化
   config_dict = settings.to_dict()

7. ⚠️  注意：BaseEnvSettings 默认 extra="allow"
   如果不需要额外的字段，记得设置 extra="ignore"

8. ✅ 自动类型转换
   - 'true', 'yes', '1' -> True
   - 'false', 'no', '0' -> False
   - '123' -> int(123)
   - '3.14' -> float(3.14)
    """)


if __name__ == "__main__":
    example_usage()
    best_practices()
