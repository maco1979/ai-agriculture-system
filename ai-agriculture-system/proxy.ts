import { type NextRequest } from "next/server";

// 简化版本：不需要 Supabase 会话更新
export async function proxy(request: NextRequest) {
  // 直接返回原始请求，不做处理
  return new Response(null, {
    status: 404,
    statusText: "Not Found",
  });
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - images - .svg, .png, .jpg, .jpeg, .gif, .webp
     */
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
