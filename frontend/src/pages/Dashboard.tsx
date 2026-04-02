'use client';

import { useProjects, useReports, useStats } from '@/hooks';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Loading } from '@/components/ui/Loading';
import { formatNumber, formatDate } from '@/lib/utils';
import {
  FolderOpen,
  Star,
  GitFork,
  FileText,
  Activity,
  CheckCircle,
  TrendingUp,
  Zap,
} from 'lucide-react';

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useStats();
  const { data: projects, isLoading: projectsLoading } = useProjects({ limit: 5 });
  const { data: reports, isLoading: reportsLoading } = useReports({ limit: 5 });

  if (statsLoading || projectsLoading || reportsLoading) {
    return <Loading />;
  }

  const avgStars = projects && projects.length > 0
    ? formatNumber(Math.round(projects.reduce((sum, p) => sum + p.stars, 0) / projects.length))
    : '0';

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="animate-fadeIn">
        <h1 className="text-3xl font-bold text-slate-800">仪表盘</h1>
        <p className="text-slate-500 mt-1">系统概览和数据统计</p>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <Card className="animate-fadeIn" style={{ animationDelay: '100ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">总项目数</CardTitle>
            <div className="p-2 rounded-lg bg-blue-50">
              <FolderOpen className="h-4 w-4 text-blue-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-800">{stats?.total_projects || 0}</div>
            <p className="text-xs text-slate-400 mt-1">已分析的项目</p>
          </CardContent>
        </Card>

        <Card className="animate-fadeIn" style={{ animationDelay: '150ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">总报告数</CardTitle>
            <div className="p-2 rounded-lg bg-cyan-50">
              <FileText className="h-4 w-4 text-cyan-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-800">{stats?.total_reports || 0}</div>
            <p className="text-xs text-slate-400 mt-1">生成的报告</p>
          </CardContent>
        </Card>

        <Card className="animate-fadeIn" style={{ animationDelay: '200ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">平均 Stars</CardTitle>
            <div className="p-2 rounded-lg bg-amber-50">
              <Star className="h-4 w-4 text-amber-500" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-slate-800">{avgStars}</div>
            <p className="text-xs text-slate-400 mt-1">Top 5 项目平均</p>
          </CardContent>
        </Card>

        <Card className="animate-fadeIn" style={{ animationDelay: '250ms' }}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">系统状态</CardTitle>
            <div className="p-2 rounded-lg bg-emerald-50">
              <CheckCircle className="h-4 w-4 text-emerald-600" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <div className="text-xl font-bold text-emerald-600">正常运行</div>
            </div>
            <p className="text-xs text-slate-400 mt-1">所有服务正常</p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Projects */}
      <Card className="animate-fadeIn" style={{ animationDelay: '300ms' }}>
        <CardHeader className="pb-4">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-500">
              <TrendingUp className="h-4 w-4 text-white" />
            </div>
            <CardTitle className="text-lg">最近项目</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {projects?.map((project, index) => (
              <div
                key={project.id}
                className="group flex items-start justify-between rounded-xl border border-slate-200/60 bg-slate-50/50 p-4 hover:bg-white hover:shadow-lg hover:border-blue-200/60 transition-all duration-300"
                style={{ animationDelay: `${350 + index * 50}ms` }}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <a
                      href={project.html_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-semibold text-blue-600 hover:text-blue-700 hover:underline transition-colors"
                    >
                      {project.full_name}
                    </a>
                    <Badge variant="secondary">Top {project.rank}</Badge>
                  </div>
                  <p className="mt-2 line-clamp-2 text-sm text-slate-500">
                    {project.description}
                  </p>
                  <div className="mt-3 flex items-center gap-4 text-xs text-slate-400">
                    <span className="flex items-center gap-1.5">
                      <Star size={12} className="text-amber-500" />
                      {formatNumber(project.stars)}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <GitFork size={12} className="text-slate-400" />
                      {formatNumber(project.forks)}
                    </span>
                    <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 font-medium">
                      {project.language}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Reports */}
      <Card className="animate-fadeIn" style={{ animationDelay: '400ms' }}>
        <CardHeader className="pb-4">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-gradient-to-br from-violet-500 to-purple-500">
              <Zap className="h-4 w-4 text-white" />
            </div>
            <CardTitle className="text-lg">最近报告</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {reports?.map((report, index) => (
              <div
                key={report.id}
                className="group flex items-start justify-between rounded-xl border border-slate-200/60 bg-slate-50/50 p-4 hover:bg-white hover:shadow-lg hover:border-violet-200/60 transition-all duration-300"
                style={{ animationDelay: `${450 + index * 50}ms` }}
              >
                <div className="flex-1">
                  <h4 className="font-semibold text-slate-700 group-hover:text-violet-700 transition-colors">
                    {report.title}
                  </h4>
                  <div className="mt-3 flex items-center gap-4 text-xs text-slate-400">
                    <span className="flex items-center gap-1.5">
                      <Activity size={12} />
                      {formatDate(report.generated_at)}
                    </span>
                    <Badge variant="success">
                      质量评分: {(report.quality_score * 100).toFixed(1)}%
                    </Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
