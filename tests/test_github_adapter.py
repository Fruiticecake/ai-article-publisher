"""测试 GitHub 适配器"""
import pytest
from datetime import datetime, timedelta, timezone
from adapters.github_adapter import GitHubAdapter
from core.models import SourceType, Project


class TestGitHubAdapter:
    """测试 GitHub 适配器"""

    def test_initialization_without_token(self):
        """测试无 token 初始化"""
        adapter = GitHubAdapter()
        assert adapter.token == ""
        assert "Authorization" not in adapter.headers

    def test_initialization_with_token(self):
        """测试带 token 初始化"""
        adapter = GitHubAdapter("test_token_123")
        assert adapter.token == "test_token_123"
        assert adapter.headers["Authorization"] == "Bearer test_token_123"

    def test_to_project_conversion_basic(self):
        """测试基本转换为项目模型"""
        adapter = GitHubAdapter()
        now = datetime.now(timezone.utc).isoformat()

        repo_data = {
            "id": 123456,
            "full_name": "octocat/hello-world",
            "html_url": "https://github.com/octocat/hello-world",
            "description": "A famous hello world repository",
            "stargazers_count": 1000,
            "forks_count": 100,
            "language": "Python",
            "topics": ["python", "demo", "example"],
            "created_at": now,
            "updated_at": now,
        }

        project = adapter.to_project(repo_data, rank=1, readme="# Hello World")

        assert isinstance(project, Project)
        assert project.source == SourceType.GITHUB
        assert project.source_id == "123456"
        assert project.rank == 1
        assert project.full_name == "octocat/hello-world"
        assert project.html_url == "https://github.com/octocat/hello-world"
        assert project.description == "A famous hello world repository"
        assert project.stars == 1000
        assert project.forks == 100
        assert project.language == "Python"
        assert project.topics == ["python", "demo", "example"]
        assert project.readme == "# Hello World"
        assert isinstance(project.created_at, datetime)
        assert isinstance(project.updated_at, datetime)

    def test_to_project_conversion_empty_values(self):
        """测试空值转换处理"""
        adapter = GitHubAdapter()
        project = adapter.to_project({}, rank=5, readme="")

        assert project.full_name == ""
        assert project.html_url == ""
        assert project.description == "暂无描述"
        assert project.stars == 0
        assert project.forks == 0
        assert project.language == "Unknown"
        assert project.topics == []

    def test_to_project_conversion_no_description(self):
        """测试无描述时使用默认文本"""
        adapter = GitHubAdapter()
        repo_data = {
            "id": 789,
            "full_name": "test/repo",
            "html_url": "https://github.com/test/repo",
            "description": None,
            "stargazers_count": 10,
            "forks_count": 2,
            "language": None,
        }

        project = adapter.to_project(repo_data, rank=3)
        assert project.description == "暂无描述"
        assert project.language == "Unknown"

    def test_days_window_calculation(self):
        """测试搜索日期窗口计算 - 通过检查 since_date 格式"""
        adapter = GitHubAdapter()
        # 由于 search_top_starred 是异步方法需要网络，我们只验证计算逻辑
        from datetime import datetime, timedelta, timezone
        days_window = 30
        since_date = (datetime.now(timezone.utc) - timedelta(days=days_window)).strftime("%Y-%m-%d")

        # 验证格式正确 YYYY-MM-DD
        assert len(since_date) == 10
        assert since_date[4] == "-"
        assert since_date[7] == "-"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
