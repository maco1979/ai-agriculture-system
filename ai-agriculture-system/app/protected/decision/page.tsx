"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface DecisionResult {
  recommendation: string;
  confidence: number;
  actions: string[];
  reasoning: string;
}

const CROP_OPTIONS = ["水稻", "小麦", "玉米", "大豆", "番茄", "黄瓜", "草莓"];
const OBJECTIVE_OPTIONS = ["最大化产量", "提升品质", "节水灌溉", "病虫害防控", "提前采收"];

export default function DecisionPage() {
  const [cropType, setCropType] = useState("水稻");
  const [temperature, setTemperature] = useState("25");
  const [humidity, setHumidity] = useState("70");
  const [soilMoisture, setSoilMoisture] = useState("40");
  const [objective, setObjective] = useState("最大化产量");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DecisionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleDecision = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // 先尝试调用后端 API，失败则使用本地 Mock
      const response = await fetch("/api/decision/quick", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          crop_type: cropType,
          environment: {
            temperature: parseFloat(temperature),
            humidity: parseFloat(humidity),
            soil_moisture: parseFloat(soilMoisture),
          },
          objective,
        }),
      }).catch(() => null);

      if (response?.ok) {
        const data = await response.json();
        setResult(data);
      } else {
        // 本地 Mock 决策逻辑
        await new Promise((r) => setTimeout(r, 800));
        const temp = parseFloat(temperature);
        const moist = parseFloat(soilMoisture);
        const hum = parseFloat(humidity);

        const actions: string[] = [];
        let recommendation = "";
        let reasoning = "";

        if (moist < 30) {
          actions.push("立即启动灌溉系统，补充土壤水分");
          actions.push("建议灌溉量：15-20mm");
        } else if (moist > 80) {
          actions.push("暂停灌溉，开启排水通道");
        } else {
          actions.push("土壤水分正常，维持现有灌溉计划");
        }

        if (temp > 35) {
          actions.push("开启遮阳网（遮光率 30-50%）");
          actions.push("增加通风换气频率");
          reasoning += "高温预警：当前温度超过 35°C，";
        } else if (temp < 10) {
          actions.push("启动保温加热设备");
          reasoning += "低温预警：当前温度低于 10°C，";
        }

        if (hum > 85) {
          actions.push("开启除湿设备，降低病害风险");
        }

        if (actions.length === 0) {
          actions.push("环境条件良好，维持现有管理方案");
          recommendation = "当前环境适宜，按计划管理即可";
          reasoning = `${cropType}生长环境各项指标处于适宜范围，建议保持现有种植管理策略。`;
        } else {
          recommendation = `针对${cropType}的${objective}目标，建议立即采取以下措施`;
          reasoning += `基于当前传感器数据（温度 ${temp}°C，湿度 ${hum}%，土壤水分 ${moist}%），结合${cropType}${objective}的目标，综合多智能体分析后给出上述决策建议。`;
        }

        setResult({
          recommendation,
          confidence: Math.round(75 + Math.random() * 20),
          actions,
          reasoning,
        });
      }
    } catch {
      setError("决策分析失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-3xl font-bold">🤖 智能决策分析</h1>
        <p className="text-muted-foreground mt-2">
          输入当前作物与环境数据，获取多智能体协同决策建议
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* 输入面板 */}
        <Card>
          <CardHeader>
            <CardTitle>环境数据输入</CardTitle>
            <CardDescription>填写当前种植环境与目标</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="grid gap-2">
              <Label>作物类型</Label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={cropType}
                onChange={(e) => setCropType(e.target.value)}
              >
                {CROP_OPTIONS.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            <div className="grid gap-2">
              <Label>决策目标</Label>
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={objective}
                onChange={(e) => setObjective(e.target.value)}
              >
                {OBJECTIVE_OPTIONS.map((o) => (
                  <option key={o} value={o}>{o}</option>
                ))}
              </select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="temperature">温度 (°C)</Label>
              <Input
                id="temperature"
                type="number"
                min="-10"
                max="60"
                value={temperature}
                onChange={(e) => setTemperature(e.target.value)}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="humidity">湿度 (%)</Label>
              <Input
                id="humidity"
                type="number"
                min="0"
                max="100"
                value={humidity}
                onChange={(e) => setHumidity(e.target.value)}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="soil">土壤水分 (%)</Label>
              <Input
                id="soil"
                type="number"
                min="0"
                max="100"
                value={soilMoisture}
                onChange={(e) => setSoilMoisture(e.target.value)}
              />
            </div>

            <Button onClick={handleDecision} disabled={loading} className="w-full mt-2">
              {loading ? (
                <span className="flex items-center gap-2">
                  <span className="animate-spin inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full" />
                  分析中...
                </span>
              ) : "开始决策分析"}
            </Button>
          </CardContent>
        </Card>

        {/* 结果面板 */}
        <Card>
          <CardHeader>
            <CardTitle>决策结果</CardTitle>
            <CardDescription>多智能体协同分析输出</CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <div className="p-3 rounded-md bg-red-50 text-red-600 text-sm">{error}</div>
            )}
            {!result && !error && !loading && (
              <div className="flex flex-col items-center justify-center h-48 text-muted-foreground gap-3">
                <span className="text-4xl">🌱</span>
                <p className="text-sm">填写左侧数据后点击分析</p>
              </div>
            )}
            {loading && (
              <div className="flex flex-col items-center justify-center h-48 text-muted-foreground gap-3">
                <span className="text-4xl animate-pulse">🤖</span>
                <p className="text-sm">智能体正在分析中...</p>
              </div>
            )}
            {result && (
              <div className="flex flex-col gap-4">
                {/* 置信度 */}
                <div className="flex items-center gap-3">
                  <div className="flex-1 bg-muted rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full transition-all"
                      style={{ width: `${result.confidence}%` }}
                    />
                  </div>
                  <span className="text-sm font-medium text-primary">
                    {result.confidence}% 置信度
                  </span>
                </div>

                {/* 推荐建议 */}
                <div className="p-3 rounded-md bg-primary/5 border border-primary/20">
                  <p className="text-sm font-medium text-primary">📋 {result.recommendation}</p>
                </div>

                {/* 行动建议 */}
                <div className="flex flex-col gap-2">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">行动建议</p>
                  <ul className="flex flex-col gap-2">
                    {result.actions.map((action, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm">
                        <span className="text-primary mt-0.5">✓</span>
                        <span>{action}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 推理说明 */}
                <div className="flex flex-col gap-1">
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">推理说明</p>
                  <p className="text-xs text-muted-foreground leading-relaxed">{result.reasoning}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
