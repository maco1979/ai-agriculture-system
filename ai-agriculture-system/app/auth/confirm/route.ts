import { redirect } from "next/navigation";
import { type NextRequest } from "next/server";

// 简化版本：无需 Supabase 验证
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const next = searchParams.get("next") ?? "/protected";

  // 直接重定向到受保护页面
  redirect(next);
}
