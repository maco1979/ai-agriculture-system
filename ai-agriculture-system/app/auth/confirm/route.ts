import { createClient } from "@/lib/supabase/server";
import { NextResponse, type NextRequest } from "next/server";

export async function GET(request: NextRequest) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/protected";

  // 防止开放重定向：只允许以 / 开头且不以 // 开头的相对路径
  const safeNext =
    next.startsWith("/") && !next.startsWith("//") ? next : "/protected";

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);

    if (!error) {
      return NextResponse.redirect(`${origin}${safeNext}`);
    }
  }

  // 出错时重定向到错误页面
  return NextResponse.redirect(`${origin}/auth/error?error=invalid_code`);
}
