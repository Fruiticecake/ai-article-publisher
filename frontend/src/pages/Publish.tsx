import { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Badge } from '../components/ui/Badge';
import { PublisherSelector } from '../components/PublisherSelector';
import { DocumentExporter } from '../components/DocumentExporter';
import { api } from '../api/client';
import type { ScheduleConfig, PublisherPlatform, PublisherInfo, Project } from '../types';

export default function Publish() {
  const [scheduleConfig, setScheduleConfig] = useState<ScheduleConfig | null>(null);
  const [publishers, setPublishers] = useState<PublisherInfo[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // 表单状态
  const [cron, setCron] = useState('0 9 * * *');
  const [timezone, setTimezone] = useState('Asia/Shanghai');
  const [enabled, setEnabled] = useState(true);
  const [selectedPlatforms, setSelectedPlatforms] = useState<PublisherPlatform[]>([]);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    // 每个请求单独处理错误，不要让一个失败导致全部失败
    const scheduleData = await api.getSchedule().catch(() => {
      setError('需要登录才能访问配置，请先登录');
      return null;
    });
    const publishersData = await api.getPublishers().catch(() => []);
    const projectsData = await api.getProjects({ limit: 20 }).catch(() => []);

    if (scheduleData) {
      setScheduleConfig(scheduleData);
      setCron(scheduleData.cron);
      setTimezone(scheduleData.timezone);
      setEnabled(scheduleData.enabled);
      setSelectedPlatforms(scheduleData.platforms || []);
    }

    setPublishers(publishersData);
    setProjects(projectsData);

    // 默认选择所有启用的平台
    const enabledPlatforms = publishersData
      .filter((p: PublisherInfo) => p.enabled)
      .map((p: PublisherInfo) => p.type);
    if (selectedPlatforms.length === 0) {
      setSelectedPlatforms(enabledPlatforms);
    }

    setLoading(false);
  };

  const handleSaveSchedule = async () => {
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await api.updateSchedule({
        cron,
        timezone,
        platforms: selectedPlatforms,
        enabled,
      });
      setSuccess('定时配置已保存');
      loadData();
    } catch (err) {
      setError('保存配置失败');
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  const handleTriggerNow = async () => {
    setTriggering(true);
    setError(null);
    setSuccess(null);

    try {
      const result = await api.triggerNow(selectedPlatforms);
      setSuccess(`任务已触发: ${result.message}`);
    } catch (err) {
      setError('触发任务失败');
      console.error(err);
    } finally {
      setTriggering(false);
    }
  };

  const togglePlatform = (platform: PublisherPlatform) => {
    setSelectedPlatforms(prev =>
      prev.includes(platform)
        ? prev.filter(p => p !== platform)
        : [...prev, platform]
    );
  };

  const getPlatformColor = (type: PublisherPlatform): string => {
    const colors: Record<PublisherPlatform, string> = {
      notion: '#000000',
      csdn: '#00a1d6',
      zhihu: '#0084ff',
      juejin: '#007fff',
      telegram: '#26a5e4',
      xhs: '#fe2c55',
    };
    return colors[type] || '#666';
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">发布中心</h1>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-600">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-600">
          {success}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 定时配置 */}
        <Card className="p-4">
          <h2 className="text-lg font-semibold mb-4">定时发布配置</h2>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">启用定时任务</span>
              <button
                onClick={() => setEnabled(!enabled)}
                className={`
                  relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                  ${enabled ? 'bg-blue-600' : 'bg-gray-300'}
                `}
              >
                <span
                  className={`
                    inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                    ${enabled ? 'translate-x-6' : 'translate-x-1'}
                  `}
                />
              </button>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Cron 表达式</label>
              <Input
                value={cron}
                onChange={(e) => setCron(e.target.value)}
                placeholder="0 9 * * *"
              />
              <p className="text-xs text-gray-500 mt-1">
                格式: 分 时 日 月 周 (默认每天 9:00 执行)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">时区</label>
              <select
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="Asia/Shanghai">Asia/Shanghai (北京时间)</option>
                <option value="UTC">UTC</option>
                <option value="America/New_York">America/New_York (美东时间)</option>
                <option value="Europe/London">Europe/London (伦敦时间)</option>
              </select>
            </div>

            <Button
              onClick={handleSaveSchedule}
              disabled={saving}
              className="w-full"
            >
              {saving ? '保存中...' : '保存配置'}
            </Button>
          </div>
        </Card>

        {/* 手动触发 */}
        <Card className="p-4">
          <h2 className="text-lg font-semibold mb-4">手动发布</h2>

          <p className="text-sm text-gray-600 mb-4">
            立即执行一次发布任务，跳过定时等待
          </p>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">选择发布平台</label>
            <div className="grid grid-cols-3 gap-2">
              {publishers.map((publisher) => {
                const isSelected = selectedPlatforms.includes(publisher.type);
                const isEnabled = publisher.enabled;

                return (
                  <button
                    key={publisher.type}
                    type="button"
                    onClick={() => isEnabled && togglePlatform(publisher.type)}
                    disabled={!isEnabled}
                    className={`
                      flex items-center gap-2 p-2 rounded-lg border-2 text-sm transition-all
                      ${isSelected
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                      }
                      ${!isEnabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                    `}
                  >
                    <span
                      className="w-5 h-5 rounded-full flex items-center justify-center text-white text-xs"
                      style={{ backgroundColor: getPlatformColor(publisher.type) }}
                    >
                    </span>
                    <span>{publisher.name}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <Button
            onClick={handleTriggerNow}
            disabled={triggering || selectedPlatforms.length === 0}
            variant="primary"
            className="w-full"
          >
            {triggering ? '执行中...' : '立即发布'}
          </Button>
        </Card>

        {/* 选择项目导出 */}
        <Card className="p-4">
          <h2 className="text-lg font-semibold mb-4">文档导出</h2>

          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">选择项目</label>
            <select
              value={selectedProject?.id || ''}
              onChange={(e) => {
                const project = projects.find(p => p.id === Number(e.target.value));
                setSelectedProject(project || null);
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">请选择项目</option>
              {projects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.full_name} (⭐{project.stars})
                </option>
              ))}
            </select>
          </div>

          {selectedProject && (
            <DocumentExporter project={selectedProject} />
          )}
        </Card>

        {/* 报告发布 */}
        <Card className="p-4">
          <h2 className="text-lg font-semibold mb-4">报告发布</h2>

          <p className="text-sm text-gray-600 mb-4">
            选择已有报告进行发布
          </p>

          <PublisherSelector
            reportId={undefined}
            onPublish={(result) => {
              setSuccess('发布成功');
            }}
          />
        </Card>
      </div>

      {/* 平台状态 */}
      <Card className="p-4 mt-6">
        <h2 className="text-lg font-semibold mb-4">平台配置状态</h2>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {publishers.map((publisher) => (
            <div
              key={publisher.type}
              className={`
                p-3 rounded-lg border text-center
                ${publisher.enabled
                  ? 'border-green-200 bg-green-50'
                  : 'border-gray-200 bg-gray-50'
                }
              `}
            >
              <div
                className="w-10 h-10 mx-auto mb-2 rounded-full flex items-center justify-center text-white font-bold"
                style={{ backgroundColor: getPlatformColor(publisher.type) }}
              >
                {publisher.name[0]}
              </div>
              <div className="font-medium text-sm">{publisher.name}</div>
              <Badge variant={publisher.enabled ? 'success' : 'secondary'}>
                {publisher.enabled ? '已启用' : '未配置'}
              </Badge>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}