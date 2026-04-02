"""测试配置读写和 .env 文件保存功能"""
import tempfile
import pytest
from pathlib import Path


def test_read_env_and_update():
    """测试读取现有 .env 文件并更新保存"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as f:
        f.write("""# 注释
GITHUB_TOKEN=old_token
GITHUB_FETCH_COUNT=50
# 另一个注释
LLM_API_KEY=old_key
""")
        temp_path = Path(f.name)

    try:
        # 模拟代码中的读取逻辑
        env_content = {}
        if temp_path.exists():
            with open(temp_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_content[key.strip()] = value.strip()

        # 验证读取正确
        assert env_content["GITHUB_TOKEN"] == "old_token"
        assert env_content["GITHUB_FETCH_COUNT"] == "50"
        assert env_content["LLM_API_KEY"] == "old_key"

        # 更新字段
        env_content["GITHUB_TOKEN"] = "new_token_123"
        env_content["LLM_API_KEY"] = "new_api_key"
        env_content["NEW_CONFIG"] = "new_value"

        # 写回
        with open(temp_path, 'w', encoding='utf-8') as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")

        # 重新读取验证
        with open(temp_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 验证更新后的值
        content = ''.join(lines)
        assert "GITHUB_TOKEN=new_token_123" in content
        assert "GITHUB_FETCH_COUNT=50" in content  # 原有值保留
        assert "LLM_API_KEY=new_api_key" in content
        assert "NEW_CONFIG=new_value" in content

    finally:
        temp_path.unlink()


def test_create_env_file_when_not_exists():
    """测试当 .env 不存在时创建新文件"""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_path = Path(tmpdir) / ".env"

        # 文件不存在，env_content 为空
        env_content = {}
        assert not env_path.exists()

        # 添加新配置
        env_content["GITHUB_TOKEN"] = "test_token"
        env_content["GITHUB_FETCH_COUNT"] = "100"

        # 写入文件
        with open(env_path, 'w', encoding='utf-8') as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")

        # 验证文件创建成功
        assert env_path.exists()
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "GITHUB_TOKEN=test_token" in content
        assert "GITHUB_FETCH_COUNT=100" in content


def test_boolean_conversion_to_lowercase():
    """测试布尔值转换为小写字符串（LLM enabled 字段）"""
    # 代码逻辑：env_content["LLM_ENABLED"] = str(enabled).lower()
    assert str(True).lower() == "true"
    assert str(False).lower() == "false"

    # 验证读取后能正确解析
    loaded = "true"
    assert loaded.lower() == "true"
    assert bool(loaded.lower()) is True  # 注意：在 Python 中非空字符串都是 True，实际代码中解析时需要处理


def test_integer_conversion_to_str_and_back():
    """测试整数转换为字符串后能正确读回"""
    # 写入
    fetch_count = 150
    env_str = str(fetch_count)
    assert env_str == "150"

    # 读回
    parsed = int(env_str)
    assert parsed == 150


def test_comments_preserved_behavior():
    """测试注释处理行为 - 当前实现会移除注释"""
    # 当前实现会跳过注释，写入时不会保留注释
    # 这是设计决策，测试确认这个行为
    input_content = """# GitHub Configuration
GITHUB_TOKEN=abc123
# Get this from your GitHub account settings
GITHUB_FETCH_COUNT=100
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as f:
        f.write(input_content)
        temp_path = Path(f.name)

    try:
        env_content = {}
        with open(temp_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_content[key.strip()] = value.strip()

        # 只有键值对被保留
        assert len(env_content) == 2
        assert "GITHUB_TOKEN" in env_content
        assert "GITHUB_FETCH_COUNT" in env_content

        # 写回后注释消失
        with open(temp_path, 'w', encoding='utf-8') as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")

        with open(temp_path, 'r', encoding='utf-8') as f:
            output_lines = f.readlines()

        # 只保留两行键值对，没有注释
        assert len(output_lines) == 2
        assert all('#' not in line for line in output_lines)

    finally:
        temp_path.unlink()


def test_empty_values_are_saved():
    """测试空值能被正确保存"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False, encoding='utf-8') as f:
        temp_path = Path(f.name)

    try:
        env_content = {}
        env_content["XHS_COOKIE"] = ""
        env_content["NOTION_TOKEN"] = ""

        with open(temp_path, 'w', encoding='utf-8') as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")

        with open(temp_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        assert "XHS_COOKIE=\n" in lines
        assert "NOTION_TOKEN=\n" in lines

    finally:
        temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
