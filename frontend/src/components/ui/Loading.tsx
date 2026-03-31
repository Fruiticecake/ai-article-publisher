export function Loading() {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="flex flex-col items-center gap-4">
        <div className="relative">
          <div className="w-12 h-12 border-4 border-slate-200 rounded-full animate-spin" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-full animate-pulse" />
        </div>
        <p className="text-sm font-medium text-slate-500 animate-pulse">加载中...</p>
      </div>
    </div>
  );
}