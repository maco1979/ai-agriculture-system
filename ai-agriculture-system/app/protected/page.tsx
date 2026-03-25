import { createClient } from "@/lib/supabase/server";
import { InfoIcon } from "lucide-react";
import { redirect } from "next/navigation";

export default async function ProtectedPage() {
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return redirect("/auth/login");
  }

  return (
    <div className="flex-1 w-full flex flex-col gap-12">
      {/* 欢迎提示 */}
      <div className="w-full">
        <div className="bg-accent text-sm p-3 px-5 rounded-md text-foreground flex gap-3 items-center">
          <InfoIcon size="16" strokeWidth={2} />
          欢迎回来，{user.email}
        </div>
      </div>

      {/* 用户信息 */}
      <div className="flex flex-col gap-4">
        <h2 className="font-bold text-2xl">账户信息</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex flex-col gap-1 p-4 rounded-xl border bg-card">
            <span className="text-xs text-muted-foreground">邮箱</span>
            <span className="font-medium">{user.email}</span>
          </div>
          <div className="flex flex-col gap-1 p-4 rounded-xl border bg-card">
            <span className="text-xs text-muted-foreground">用户 ID</span>
            <span className="font-mono text-sm break-all">{user.id}</span>
          </div>
          <div className="flex flex-col gap-1 p-4 rounded-xl border bg-card">
            <span className="text-xs text-muted-foreground">注册时间</span>
            <span className="font-medium">
              {new Date(user.created_at).toLocaleDateString("zh-CN", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </span>
          </div>
          <div className="flex flex-col gap-1 p-4 rounded-xl border bg-card">
            <span className="text-xs text-muted-foreground">上次登录</span>
            <span className="font-medium">
              {user.last_sign_in_at
                ? new Date(user.last_sign_in_at).toLocaleString("zh-CN")
                : "—"}
            </span>
          </div>
        </div>
      </div>

      {/* 功能入口 */}
      <div className="flex flex-col gap-4">
        <h2 className="font-bold text-2xl">功能模块</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex flex-col gap-3 p-6 rounded-xl border bg-card hover:shadow-md transition-shadow cursor-pointer">
            <span className="text-2xl">🤖</span>
            <h3 className="font-semibold">智能决策</h3>
            <p className="text-sm text-muted-foreground">多智能体协同农业决策分析</p>
          </div>
          <div className="flex flex-col gap-3 p-6 rounded-xl border bg-card hover:shadow-md transition-shadow cursor-pointer">
            <span className="text-2xl">📊</span>
            <h3 className="font-semibold">数据监控</h3>
            <p className="text-sm text-muted-foreground">实时传感器数据与作物状态</p>
          </div>
          <div className="flex flex-col gap-3 p-6 rounded-xl border bg-card hover:shadow-md transition-shadow cursor-pointer">
            <span className="text-2xl">📷</span>
            <h3 className="font-semibold">摄像头控制</h3>
            <p className="text-sm text-muted-foreground">PTZ 云台控制与 AI 病害检测</p>
          </div>
        </div>
      </div>
    </div>
  );
}
