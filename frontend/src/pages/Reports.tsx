'use client';

import { useReports } from '@/hooks/useReports';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Loading } from '@/components/ui/Loading';
import { formatDate } from '@/lib/utils';

export default function Reports() {
  const { data: reports, isLoading } = useReports({ limit: 50 });

  if (isLoading) return <Loading />;

  return (
    <div className="space-y-6">
      <div data-testid="reports-header">
        <h1 className="text-2xl font-bold text-gray-900">报告列表</h1>
        <p className="text-gray-600">所有生成的分析报告</p>
      </div>

      <Card data-testid="reports-card">
        <CardContent className="p-6">
          <div className="space-y-4" data-testid="reports-list">
            {reports?.map((report, index) => (
              <div
                key={report.id}
                className="flex items-start justify-between rounded-lg border bg-white p-4 hover:shadow-md transition-shadow"
                data-testid={`report-item-${index}`}
              >
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900" data-testid={`report-title-${index}`}>{report.title}</h4>
                  <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                    <span>生成时间: {formatDate(report.generated_at)}</span>
                    <Badge variant="success">
                      质量评分: {(report.quality_score * 100).toFixed(1)}%
                    </Badge>
                  </div>
                  {report.insights && report.insights.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs text-gray-600 mb-1">洞察:</p>
                      <ul className="list-disc list-inside text-xs text-gray-600 space-y-1">
                        {report.insights.slice(0, 3).map((insight, i) => (
                          <li key={i}>{insight}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
