import { Badge } from "./ui/badge";

export function EnvVarWarning() {
  return (
    <div className="flex gap-4 items-center">
      <Badge variant={"outline"} className="font-normal text-yellow-600 border-yellow-400">
        ⚠️ 未配置 Supabase 环境变量
      </Badge>
    </div>
  );
}
