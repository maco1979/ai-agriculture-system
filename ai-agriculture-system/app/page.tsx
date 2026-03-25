import { AuthButton } from "@/components/auth-button";
import { ThemeSwitcher } from "@/components/theme-switcher";
import Link from "next/link";
import { Suspense } from "react";

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center">
      <div className="flex-1 w-full flex flex-col gap-20 items-center">
        {/* 导航栏 */}
        <nav className="w-full flex justify-center border-b border-b-foreground/10 h-16">
          <div className="w-full max-w-5xl flex justify-between items-center p-3 px-5 text-sm">
            <div className="flex gap-5 items-center font-semibold">
              <Link href="/" className="text-foreground hover:opacity-80 transition-opacity">
                🌱 AI 农业智能决策系统
              </Link>
            </div>
            <div className="flex items-center gap-4">
              <ThemeSwitcher />
              <Suspense>
                <AuthButton />
              </Suspense>
            </div>
          </div>
        </nav>

        {/* Hero 区域 */}
        <div className="flex-1 flex flex-col gap-16 max-w-5xl p-5 items-center justify-center text-center">
          <div className="flex flex-col gap-6 items-center">
            <div className="text-6xl">🌾</div>
            <h1 className="text-4xl lg:text-5xl font-bold !leading-tight max-w-2xl">
              AI 驱动的农业智能决策平台
            </h1>
            <p className="text-lg text-muted-foreground max-w-xl leading-relaxed">
              融合联邦学习、边缘计算与多智能体协同，为农业生产提供精准的种植决策、
              病虫害预测与灌溉施肥方案。
            </p>
          </div>

          {/* 功能卡片 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full">
            <div className="flex flex-col gap-3 p-6 rounded-xl border bg-card hover:shadow-md transition-shadow">
              <span className="text-3xl">🤖</span>
              <h3 className="font-semibold text-lg">多智能体协同决策</h3>
              <p className="text-sm text-muted-foreground">
                集成气候、土壤、作物、设备等专业智能体，通过协同推理输出最优种植方案
              </p>
            </div>
            <div className="flex flex-col gap-3 p-6 rounded-xl border bg-card hover:shadow-md transition-shadow">
              <span className="text-3xl">📷</span>
              <h3 className="font-semibold text-lg">实时摄像头监控</h3>
              <p className="text-sm text-muted-foreground">
                支持 PTZ 云台控制与 AI 视觉分析，实时检测作物病害与生长状态
              </p>
            </div>
            <div className="flex flex-col gap-3 p-6 rounded-xl border bg-card hover:shadow-md transition-shadow">
              <span className="text-3xl">🔗</span>
              <h3 className="font-semibold text-lg">区块链溯源</h3>
              <p className="text-sm text-muted-foreground">
                基于 Hyperledger Fabric 的农产品全链路溯源，确保数据不可篡改
              </p>
            </div>
          </div>

          {/* CTA 按钮 */}
          <div className="flex gap-4">
            <Link
              href="/auth/sign-up"
              className="inline-flex items-center justify-center rounded-md text-sm font-medium h-10 px-6 bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              立即开始
            </Link>
            <Link
              href="/auth/login"
              className="inline-flex items-center justify-center rounded-md text-sm font-medium h-10 px-6 border border-input bg-background hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              登录系统
            </Link>
          </div>
        </div>

        {/* 页脚 */}
        <footer className="w-full flex items-center justify-center border-t text-center text-xs text-muted-foreground gap-8 py-10">
          <p>AI 农业智能决策系统 &copy; {new Date().getFullYear()}</p>
          <ThemeSwitcher />
        </footer>
      </div>
    </main>
  );
}
