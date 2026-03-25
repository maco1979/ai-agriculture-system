import { ThemeSwitcher } from "@/components/theme-switcher";
import { LogoutButton } from "@/components/logout-button";
import Link from "next/link";

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
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
              <LogoutButton />
            </div>
          </div>
        </nav>

        <div className="flex-1 flex flex-col gap-20 max-w-5xl w-full p-5">
          {children}
        </div>

        {/* 页脚 */}
        <footer className="w-full flex items-center justify-center border-t text-center text-xs text-muted-foreground gap-8 py-10">
          <p>AI 农业智能决策系统 &copy; {new Date().getFullYear()}</p>
        </footer>
      </div>
    </main>
  );
}
