"use client";

import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

export function LogoutButton() {
  const router = useRouter();

  const logout = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/auth/login");
    router.refresh();
  };

  return (
    <Button onClick={logout} variant="outline" size="sm">
      退出登录
    </Button>
  );
}
