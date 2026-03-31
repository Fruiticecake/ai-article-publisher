import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';

export default function Settings() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">设置</h1>
        <p className="text-gray-600">系统配置和偏好设置</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>系统信息</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">版本</span>
              <span className="text-sm font-medium">1.0.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-gray-600">API 地址</span>
              <span className="text-sm font-medium">http://localhost:8080</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
