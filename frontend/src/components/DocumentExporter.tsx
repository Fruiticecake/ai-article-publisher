import { useState } from 'react';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { api, downloadBlob } from '../api/client';
import type { Project, ExportFormat } from '../types';

interface DocumentExporterProps {
  project: Project;
}

export function DocumentExporter({ project }: DocumentExporterProps) {
  const [exporting, setExporting] = useState<ExportFormat | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async (format: ExportFormat) => {
    setExporting(format);
    setError(null);

    try {
      const response = await api.exportDocument(project.id, format);
      const blob = new Blob([response.data], {
        type: format === 'pdf' ? 'application/pdf' : 'text/markdown',
      });
      const filename = `${project.full_name.replace('/', '_')}_${new Date().toISOString().split('T')[0]}.${format}`;
      downloadBlob(blob, filename);
    } catch (err) {
      setError(`导出${format.toUpperCase()}失败，请重试`);
      console.error(err);
    } finally {
      setExporting(null);
    }
  };

  return (
    <Card className="p-4">
      <h3 className="text-lg font-semibold mb-4">文档导出</h3>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
          {error}
        </div>
      )}

      <p className="text-sm text-gray-600 mb-4">
        将项目分析报告导出为不同格式
      </p>

      <div className="space-y-3">
        <Button
          onClick={() => handleExport('pdf')}
          disabled={exporting !== null}
          variant="secondary"
          className="w-full justify-center"
        >
          {exporting === 'pdf' ? '导出中...' : '📄 导出 PDF'}
        </Button>

        <Button
          onClick={() => handleExport('markdown')}
          disabled={exporting !== null}
          variant="secondary"
          className="w-full justify-center"
        >
          {exporting === 'markdown' ? '导出中...' : '📝 导出 Markdown'}
        </Button>
      </div>

      <div className="mt-4 text-xs text-gray-500">
        <p>PDF 格式适合打印和分享</p>
        <p>Markdown 格式适合编辑和二次创作</p>
      </div>
    </Card>
  );
}