'use client';

import { useProjects } from '@/hooks/useProjects';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Loading } from '@/components/ui/Loading';
import { formatNumber, formatDate } from '@/lib/utils';
import { Star, GitFork, ExternalLink, Search, Filter } from 'lucide-react';

export default function Projects() {
  const { data: projects, isLoading } = useProjects({ limit: 50 });

  if (isLoading) return <Loading />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between" data-testid="projects-header">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">项目列表</h1>
          <p className="text-slate-500 mt-1">所有已分析的 GitHub 项目</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="搜索项目..."
              className="h-10 pl-10 pr-4 rounded-xl border border-slate-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 w-64"
              data-testid="search-input"
            />
          </div>
          <button className="flex items-center gap-2 h-10 px-4 rounded-xl border border-slate-200 bg-white text-sm text-slate-600 hover:bg-slate-50 transition-colors" data-testid="filter-button">
            <Filter size={16} />
            筛选
          </button>
        </div>
      </div>

      <Card data-testid="projects-card">
        <CardContent className="p-6">
          <div className="space-y-3" data-testid="projects-list">
            {projects?.map((project, index) => (
              <div
                key={project.id}
                className="group flex items-start justify-between rounded-xl border border-slate-200/60 bg-slate-50/50 p-5 hover:bg-white hover:shadow-lg hover:border-blue-200/60 transition-all duration-300"
                data-testid={`project-item-${index}`}
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <a
                      href={project.html_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-semibold text-blue-600 hover:text-blue-700 hover:underline transition-colors"
                      data-testid={`project-name-${index}`}
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
                    <span className="text-slate-400">
                      {formatDate(project.created_at)}
                    </span>
                  </div>
                </div>
                <a
                  href={project.html_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-2 rounded-lg text-slate-400 hover:text-blue-600 hover:bg-blue-50 transition-all duration-200"
                >
                  <ExternalLink size={18} />
                </a>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
