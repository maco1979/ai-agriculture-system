import { createClient } from "@/lib/supabase/server";
import { InfoIcon } from "lucide-react";
import { redirect } from "next/navigation";
import Link from "next/link";

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
          <Link href="/protected/decision" className="block">
            <div className="flex flex-col gap-3 p-6 rounded-xl border bg-card hover:shadow-md hover:border-primary/50 transition-all cursor-pointer h-full">
              <span className="text-2xl">🤖</span>
              <h3 className="font-semibold">智能决策</h3>
              <p className="text-sm text-muted-foreground">多智能体协同农业决策分析</p>
              <span className="text-xs text-primary mt-auto">进入模块 →</span>
            </div>
          </Link>
          <Link href="/protected/monitor" className="block">
            <div className="flex flex-col gap-3 p-6 rounded-xl border bg-card hover:shadow-md hover:border-primary/50 transition-all cursor-pointer h-full">
              <span className="text-2xl">📊</span>
              <h3 className="font-semibold">数据监控</h3>
              <p className="text-sm text-muted-foreground">实时传感器数据与作物状态</p>
              <span className="text-xs text-primary mt-auto">进入模块 →</span>
            </div>
          </Link>
          <Link href="/protected/camera" className="block">
            <div className="flex flex-col gap-3 p-6 rounded-xl border bg-card hover:shadow-md hover:border-primary/50 transition-all cursor-pointer h-full">
              <span className="text-2xl">📷</span>
              <h3 className="font-semibold">摄像头控制</h3>
              <p className="text-sm text-muted-foreground">PTZ 云台控制与 AI 病害检测</p>
              <span className="text-xs text-primary mt-auto">进入模块 →</span>
            </div>
          </Link>
        </div>
      </div>

      {/* 系统状态 */}
      <div className="flex flex-col gap-4">
        <h2 className="font-bold text-2xl">系统状态</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: "智能体在线", value: "6/6", color: "text-green-500" },
            { label: "传感器节点", value: "12 个", color: "text-blue-500" },
            { label: "今日决策次数", value: "48", color: "text-purple-500" },
            { label: "系统健康度", value: "100%", color: "text-green-500" },
          ].map((item) => (
            <div key={item.label} className="flex flex-col gap-1 p-4 rounded-xl border bg-card">
              <span className="text-xs text-muted-foreground">{item.label}</span>
              <span className={`text-xl font-bold ${item.color}`}>{item.value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
