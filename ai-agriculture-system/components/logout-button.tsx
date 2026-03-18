"use client";

import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";

export function LogoutButton() {
  const router = useRouter();

  const logout = async () => {
    // 简单的模拟退出
    router.push("/auth/login");
  };

  return <Button onClick={logout}>Logout</Button>;
}
