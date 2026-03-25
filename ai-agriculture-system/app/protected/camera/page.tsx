"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const PRESET_CAMERAS = [
  { id: "cam-01", name: "温室 A 区 - 正前方", status: "online" },
  { id: "cam-02", name: "温室 B 区 - 全景", status: "online" },
  { id: "cam-03", name: "室外气象站", status: "offline" },
];

const PTZ_ACTIONS = [
  { label: "↑", action: "up", title: "向上" },
  { label: "↓", action: "down", title: "向下" },
  { label: "←", action: "left", title: "向左" },
  { label: "→", action: "right", title: "向右" },
  { label: "🔍+", action: "zoom-in", title: "放大" },
  { label: "🔍-", action: "zoom-out", title: "缩小" },
  { label: "⏺", action: "preset-1", title: "预置位 1" },
  { label: "🏠", action: "home", title: "归位" },
];

const AI_RESULTS = [
  { label: "作物健康度", value: "92%", color: "text-green-500" },
  { label: "病害检测", value: "未发现", color: "text-green-500" },
  { label: "生长阶段", value: "营养生长期", color: "text-blue-500" },
  { label: "覆盖率", value: "78%", color: "text-purple-500" },
];

export default function CameraPage() {
  const [selectedCam, setSelectedCam] = useState(PRESET_CAMERAS[0]);
  const [lastAction, setLastAction] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(false);

  const handlePtz = (action: string, title: string) => {
    setLastAction(`PTZ 控制：${title}`);
    setTimeout(() => setLastAction(null), 2000);
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    await new Promise((r) => setTimeout(r, 1500));
    setAnalyzing(false);
    setAnalysisResult(true);
  };

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-3xl font-bold">📷 摄像头控制</h1>
        <p className="text-muted-foreground mt-2">PTZ 云台控制与 AI 视觉病害检测</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 摄像头列表 */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">摄像头列表</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {PRESET_CAMERAS.map((cam) => (
              <button
                key={cam.id}
                onClick={() => {
                  if (cam.status === "online") {
                    setSelectedCam(cam);
                    setAnalysisResult(false);
                  }
                }}
                className={`w-full text-left p-3 rounded-lg border text-sm transition-all ${
                  selectedCam.id === cam.id
                    ? "border-primary bg-primary/5"
                    : "border-transparent hover:border-muted-foreground/30"
                } ${cam.status === "offline" ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">{cam.name}</span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full ${
                      cam.status === "online"
                        ? "bg-green-100 text-green-700"
                        : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    {cam.status === "online" ? "在线" : "离线"}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">{cam.id}</p>
              </button>
            ))}
          </CardContent>
        </Card>

        {/* 视频预览 */}
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-base flex items-center justify-between">
              <span>{selectedCam.name}</span>
              <span className="text-xs text-green-600 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse inline-block" />
                实时
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {/* 模拟视频画面 */}
            <div className="aspect-video bg-gradient-to-br from-green-900 via-green-800 to-green-700 rounded-lg flex items-center justify-center relative overflow-hidden">
              <div className="absolute inset-0 opacity-10"
                style={{
                  backgroundImage: "repeating-linear-gradient(0deg, #00ff00 0, #00ff00 1px, transparent 1px, transparent 20px), repeating-linear-gradient(90deg, #00ff00 0, #00ff00 1px, transparent 1px, transparent 20px)",
                }}
              />
              <div className="text-center text-white/80 z-10">
                <div className="text-5xl mb-3">🌿</div>
                <p className="text-sm font-medium">实时视频流</p>
                <p className="text-xs opacity-60 mt-1">{selectedCam.name}</p>
              </div>
              {/* 时间戳 */}
              <div className="absolute bottom-3 right-3 text-xs text-white/60 font-mono">
                {new Date().toLocaleString("zh-CN")}
              </div>
              {/* 正在操作提示 */}
              {lastAction && (
                <div className="absolute top-3 left-3 bg-black/60 text-white text-xs px-2 py-1 rounded">
                  {lastAction}
                </div>
              )}
            </div>

            {/* PTZ 控制 */}
            <div className="flex flex-wrap gap-2">
              {PTZ_ACTIONS.map((btn) => (
                <button
                  key={btn.action}
                  onClick={() => handlePtz(btn.action, btn.title)}
                  title={btn.title}
                  className="w-10 h-10 rounded-lg border bg-background hover:bg-accent text-sm font-medium transition-colors"
                >
                  {btn.label}
                </button>
              ))}
            </div>

            {/* AI 分析 */}
            <Button onClick={handleAnalyze} disabled={analyzing} variant="outline">
              {analyzing ? (
                <span className="flex items-center gap-2">
                  <span className="animate-spin inline-block w-4 h-4 border-2 border-current border-t-transparent rounded-full" />
                  AI 分析中...
                </span>
              ) : "🔬 AI 视觉分析"}
            </Button>

            {analysisResult && (
              <div className="grid grid-cols-2 gap-3">
                {AI_RESULTS.map((r) => (
                  <div key={r.label} className="flex flex-col gap-1 p-3 rounded-lg bg-muted/50">
                    <p className="text-xs text-muted-foreground">{r.label}</p>
                    <p className={`font-semibold ${r.color}`}>{r.value}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
