'use client';

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { api } from '@/api/client';
import type { GithubConfig, LlmConfig, PublisherConfig } from '@/types';
import { toast } from 'react-hot-toast';
import { Save, RefreshCw, Eye, EyeOff } from 'lucide-react';

export default function Settings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});

  // 配置状态
  const [githubConfig, setGithubConfig] = useState<GithubConfig>({
    token: '',
    fetch_count: 100,
    days_window: 30,
  });

  const [llmConfig, setLlmConfig] = useState<LlmConfig>({
    api_key: '',
    model: 'claude-3-5-sonnet-20241022',
    enabled: false,
  });

  const [publisherConfig, setPublisherConfig] = useState<PublisherConfig>({
    notion_token: '',
    notion_database_id: '',
    csdn_api: '',
    csdn_token: '',
    zhihu_token: '',
    juejin_token: '',
    telegram_bot_token: '',
    telegram_chat_id: '',
    xhs_cookie: '',
  });

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const [github, llm, publishers] = await Promise.all([
        api.getGithubConfig().catch(() => ({ token: '', fetch_count: 100, days_window: 30 })),
        api.getLlmConfig().catch(() => ({ api_key: '', model: 'claude-3-5-sonnet-20241022', enabled: false })),
        api.getPublisherConfig().catch(() => ({
          notion_token: '', notion_database_id: '', csdn_api: '', csdn_token: '',
          zhihu_token: '', juejin_token: '', telegram_bot_token: '', telegram_chat_id: '', xhs_cookie: '',
        })),
      ]);
      setGithubConfig(github);
      setLlmConfig(llm);
      setPublisherConfig(publishers);
    } catch (err) {
      toast.error('加载配置失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSecret = (key: string) => {
    setShowSecrets(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const saveAllConfig = async () => {
    setSaving(true);
    try {
      await Promise.all([
        api.updateGithubConfig(githubConfig),
        api.updateLlmConfig(llmConfig),
        api.updatePublisherConfig(publisherConfig),
      ]);
      toast.success('所有配置已保存！部分配置可能需要重启服务器生效');
    } catch (err) {
      toast.error('保存配置失败');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-500">加载配置中...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between" data-testid="settings-header">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">系统设置</h1>
          <p className="text-gray-600">配置 API Keys、Tokens 和各项参数</p>
        </div>
        <Button
          onClick={saveAllConfig}
          disabled={saving}
          variant="default"
          className="flex items-center gap-2"
          data-testid="save-all-button"
        >
          <Save className="w-4 h-4" />
          {saving ? '保存中...' : '保存所有配置'}
        </Button>
      </div>

      {/* GitHub 配置 */}
      <Card data-testid="github-config-card">
        <CardHeader>
          <CardTitle>GitHub 配置</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1 text-gray-700">GitHub Token</label>
            <div className="relative">
              <Input
                type={showSecrets.github_token ? 'text' : 'password'}
                value={githubConfig.token}
                onChange={(e) => setGithubConfig({ ...githubConfig, token: e.target.value })}
                placeholder="ghp_..."
                className="pr-12"
                data-testid="github-token-input"
              />
              <button
                type="button"
                onClick={() => toggleSecret('github_token')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showSecrets.github_token ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              GitHub 个人访问令牌，用于获取 trending 项目数据
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700">获取数量</label>
              <Input
                type="number"
                value={githubConfig.fetch_count}
                onChange={(e) => setGithubConfig({ ...githubConfig, fetch_count: Number(e.target.value) })}
                placeholder="100"
              />
              <p className="text-xs text-gray-500 mt-1">
                每次获取多少个 trending 项目
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700">时间窗口（天）</label>
              <Input
                type="number"
                value={githubConfig.days_window}
                onChange={(e) => setGithubConfig({ ...githubConfig, days_window: Number(e.target.value) })}
                placeholder="30"
              />
              <p className="text-xs text-gray-500 mt-1">
                只获取最近 N 天内创建的项目
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* LLM 配置 */}
      <Card>
        <CardHeader>
          <CardTitle>LLM / AI 配置</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1 text-gray-700">Anthropic API Key</label>
            <div className="relative">
              <Input
                type={showSecrets.llm_api_key ? 'text' : 'password'}
                value={llmConfig.api_key}
                onChange={(e) => setLlmConfig({ ...llmConfig, api_key: e.target.value })}
                placeholder="sk-ant-..."
                className="pr-12"
              />
              <button
                type="button"
                onClick={() => toggleSecret('llm_api_key')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {showSecrets.llm_api_key ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-1 text-gray-700">Model Name</label>
            <Input
              type="text"
              value={llmConfig.model}
              onChange={(e) => setLlmConfig({ ...llmConfig, model: e.target.value })}
              placeholder="claude-3-5-sonnet-20241022"
            />
            <p className="text-xs text-gray-500 mt-1">
              使用的 Claude 模型名称
            </p>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm font-medium text-gray-700">启用 LLM 分析</span>
              <p className="text-xs text-gray-500">禁用后将不进行 AI 分析，只收集数据</p>
            </div>
            <button
              onClick={() => setLlmConfig({ ...llmConfig, enabled: !llmConfig.enabled })}
              className={`
                relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                ${llmConfig.enabled ? 'bg-blue-600' : 'bg-gray-300'}
              `}
            >
              <span
                className={`
                  inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                  ${llmConfig.enabled ? 'translate-x-6' : 'translate-x-1'}
                `}
              />
            </button>
          </div>
        </CardContent>
      </Card>

      {/* 发布平台配置 */}
      <Card>
        <CardHeader>
          <CardTitle>发布平台配置</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Notion */}
            <div className="space-y-3">
              <h3 className="font-medium text-sm">Notion</h3>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Integration Token</label>
                <div className="relative">
                  <Input
                    type={showSecrets.notion_token ? 'text' : 'password'}
                    value={publisherConfig.notion_token}
                    onChange={(e) => setPublisherConfig({ ...publisherConfig, notion_token: e.target.value })}
                    className="pr-12 text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => toggleSecret('notion_token')}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400"
                  >
                    {showSecrets.notion_token ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Database ID</label>
                <Input
                  type="text"
                  value={publisherConfig.notion_database_id}
                  onChange={(e) => setPublisherConfig({ ...publisherConfig, notion_database_id: e.target.value })}
                  className="text-sm"
                />
              </div>
            </div>

            {/* CSDN */}
            <div className="space-y-3">
              <h3 className="font-medium text-sm">CSDN</h3>
              <div>
                <label className="block text-xs text-gray-600 mb-1">API URL</label>
                <Input
                  type="text"
                  value={publisherConfig.csdn_api}
                  onChange={(e) => setPublisherConfig({ ...publisherConfig, csdn_api: e.target.value })}
                  className="text-sm"
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Access Token</label>
                <div className="relative">
                  <Input
                    type={showSecrets.csdn_token ? 'text' : 'password'}
                    value={publisherConfig.csdn_token}
                    onChange={(e) => setPublisherConfig({ ...publisherConfig, csdn_token: e.target.value })}
                    className="pr-12 text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => toggleSecret('csdn_token')}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400"
                  >
                    {showSecrets.csdn_token ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  </button>
                </div>
              </div>
            </div>

            {/* 知乎 */}
            <div className="space-y-3">
              <h3 className="font-medium text-sm">知乎</h3>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Access Token</label>
                <div className="relative">
                  <Input
                    type={showSecrets.zhihu_token ? 'text' : 'password'}
                    value={publisherConfig.zhihu_token}
                    onChange={(e) => setPublisherConfig({ ...publisherConfig, zhihu_token: e.target.value })}
                    className="pr-12 text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => toggleSecret('zhihu_token')}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400"
                  >
                    {showSecrets.zhihu_token ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  </button>
                </div>
              </div>
            </div>

            {/* 掘金 */}
            <div className="space-y-3">
              <h3 className="font-medium text-sm">掘金</h3>
              <div>
                <label className="block text-xs text-gray-600 mb-1">User Token</label>
                <div className="relative">
                  <Input
                    type={showSecrets.juejin_token ? 'text' : 'password'}
                    value={publisherConfig.juejin_token}
                    onChange={(e) => setPublisherConfig({ ...publisherConfig, juejin_token: e.target.value })}
                    className="pr-12 text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => toggleSecret('juejin_token')}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400"
                  >
                    {showSecrets.juejin_token ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  </button>
                </div>
              </div>
            </div>

            {/* Telegram */}
            <div className="space-y-3">
              <h3 className="font-medium text-sm">Telegram</h3>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Bot Token</label>
                <div className="relative">
                  <Input
                    type={showSecrets.telegram_bot_token ? 'text' : 'password'}
                    value={publisherConfig.telegram_bot_token}
                    onChange={(e) => setPublisherConfig({ ...publisherConfig, telegram_bot_token: e.target.value })}
                    className="pr-12 text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => toggleSecret('telegram_bot_token')}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400"
                  >
                    {showSecrets.telegram_bot_token ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Chat ID</label>
                <Input
                  type="text"
                  value={publisherConfig.telegram_chat_id}
                  onChange={(e) => setPublisherConfig({ ...publisherConfig, telegram_chat_id: e.target.value })}
                  className="text-sm"
                />
              </div>
            </div>

            {/* 小红书 */}
            <div className="space-y-3">
              <h3 className="font-medium text-sm">小红书</h3>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Cookie</label>
                <div className="relative">
                  <Input
                    type={showSecrets.xhs_cookie ? 'text' : 'password'}
                    value={publisherConfig.xhs_cookie}
                    onChange={(e) => setPublisherConfig({ ...publisherConfig, xhs_cookie: e.target.value })}
                    className="pr-12 text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => toggleSecret('xhs_cookie')}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400"
                  >
                    {showSecrets.xhs_cookie ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  从浏览器复制的小红书登录 Cookie
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 系统信息 */}
      <Card>
        <CardHeader>
          <CardTitle>系统信息</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">版本</span>
              <span className="font-medium">2.0.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">API 地址</span>
              <span className="font-medium">http://localhost:8080/api</span>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button
          onClick={saveAllConfig}
          disabled={saving}
          variant="default"
          className="flex items-center gap-2 w-48"
        >
          <RefreshCw className={`w-4 h-4 ${saving ? 'animate-spin' : ''}`} />
          {saving ? '保存中...' : '保存所有配置'}
        </Button>
      </div>
    </div>
  );
}
