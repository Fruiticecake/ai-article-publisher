'use client';

import { useState, useEffect } from 'react';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { api } from '../api/client';
import type { PublisherInfo, PublisherPlatform, PublishResponse } from '../types';

interface PublisherSelectorProps {
  reportId?: number;
  onPublish?: (result: PublishResponse) => void;
}

export function PublisherSelector({ reportId, onPublish }: PublisherSelectorProps) {
  const [publishers, setPublishers] = useState<PublisherInfo[]>([]);
  const [selectedPlatforms, setSelectedPlatforms] = useState<PublisherPlatform[]>([]);
  const [loading, setLoading] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [publishResult, setPublishResult] = useState<PublishResponse | null>(null);

  useEffect(() => {
    loadPublishers();
  }, []);

  const loadPublishers = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getPublishers();
      setPublishers(data);
      // 默认选择所有启用的平台
      const enabledPlatforms = data
        .filter((p: PublisherInfo) => p.enabled)
        .map((p: PublisherInfo) => p.type);
      setSelectedPlatforms(enabledPlatforms);
    } catch (err) {
      setError('加载发布平台失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const togglePlatform = (platform: PublisherPlatform) => {
    setSelectedPlatforms(prev =>
      prev.includes(platform)
        ? prev.filter(p => p !== platform)
        : [...prev, platform]
    );
  };

  const handlePublish = async () => {
    if (!reportId) {
      setError('请先选择一个报告');
      return;
    }

    if (selectedPlatforms.length === 0) {
      setError('请至少选择一个发布平台');
      return;
    }

    setPublishing(true);
    setError(null);
    setPublishResult(null);

    try {
      const result = await api.publishReport(reportId, selectedPlatforms);
      setPublishResult(result);
      onPublish?.(result);
    } catch (err) {
      setError('发布失败，请重试');
      console.error(err);
    } finally {
      setPublishing(false);
    }
  };

  const getPlatformIcon = (type: PublisherPlatform): string => {
    const icons: Record<PublisherPlatform, string> = {
      notion: 'N',
      csdn: 'C',
      zhihu: '知',
      juejin: '掘',
      telegram: 'TG',
      xhs: '小红',
    };
    return icons[type] || type;
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
      <Card className="p-4">
        <div className="text-center text-gray-500">加载中...</div>
      </Card>
    );
  }

  return (
    <Card className="p-4">
      <h3 className="text-lg font-semibold mb-4">发布平台</h3>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
          {error}
        </div>
      )}

      {publishResult && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-600 text-sm">
          发布成功！已发布到 {Object.keys(publishResult.platforms).length} 个平台
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 mb-4">
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
                flex items-center gap-3 p-3 rounded-lg border-2 transition-all
                ${isSelected
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
                }
                ${!isEnabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <span
                className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold"
                style={{ backgroundColor: getPlatformColor(publisher.type) }}
              >
                {getPlatformIcon(publisher.type)}
              </span>
              <div className="flex-1 text-left">
                <div className="font-medium text-sm">{publisher.name}</div>
                <div className="text-xs text-gray-500">
                  {isEnabled ? '已配置' : '未配置'}
                </div>
              </div>
              {isSelected && isEnabled && (
                <span className="text-blue-500">✓</span>
              )}
            </button>
          );
        })}
      </div>

      <Button
        onClick={handlePublish}
        disabled={publishing || selectedPlatforms.length === 0 || !reportId}
        className="w-full"
      >
        {publishing ? '发布中...' : `发布到 ${selectedPlatforms.length} 个平台`}
      </Button>
    </Card>
  );
}