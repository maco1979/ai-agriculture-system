"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface SensorData {
  temperature: number;
  humidity: number;
  soil_moisture: number;
  co2: number;
  light: number;
  timestamp: string;
}

function randomSensor(): SensorData {
  return {
    temperature: parseFloat((20 + Math.random() * 15).toFixed(1)),
    humidity: parseFloat((50 + Math.random() * 40).toFixed(1)),
    soil_moisture: parseFloat((30 + Math.random() * 50).toFixed(1)),
    co2: parseFloat((380 + Math.random() * 120).toFixed(0)),
    light: parseFloat((200 + Math.random() * 800).toFixed(0)),
    timestamp: new Date().toLocaleTimeString("zh-CN"),
  };
}

function StatusDot({ value, min, max }: { value: number; min: number; max: number }) {
  const ok = value >= min && value <= max;
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${ok ? "bg-green-500" : "bg-red-500"}`}
    />
  );
}

export default function MonitorPage() {
  const [data, setData] = useState<SensorData>(randomSensor());
  const [history, setHistory] = useState<SensorData[]>([]);

  useEffect(() => {
    setHistory([randomSensor(), randomSensor(), randomSensor()]);
    const timer = setInterval(() => {
      const next = randomSensor();
      setData(next);
      setHistory((prev) => [next, ...prev.slice(0, 9)]);
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  const sensors = [
    { key: "temperature", label: "温度", value: data.temperature, unit: "°C", min: 15, max: 35, icon: "🌡️" },
    { key: "humidity", label: "湿度", value: data.humidity, unit: "%", min: 40, max: 80, icon: "💧" },
    { key: "soil_moisture", label: "土壤水分", value: data.soil_moisture, unit: "%", min: 30, max: 70, icon: "🌱" },
    { key: "co2", label: "CO₂ 浓度", value: data.co2, unit: "ppm", min: 350, max: 500, icon: "☁️" },
    { key: "light", label: "光照强度", value: data.light, unit: "lux", min: 300, max: 900, icon: "☀️" },
  ];

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">📊 数据监控</h1>
          <p className="text-muted-foreground mt-2">实时传感器数据（每 5 秒刷新）</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-green-600">
          <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse inline-block" />
          实时连接中
        </div>
      </div>

      {/* 传感器卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {sensors.map((s) => {
          const ok = s.value >= s.min && s.value <= s.max;
          return (
            <Card key={s.key} className={ok ? "" : "border-red-300"}>
              <CardContent className="p-4 flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="text-xl">{s.icon}</span>
                  <StatusDot value={s.value} min={s.min} max={s.max} />
                </div>
                <p className="text-xs text-muted-foreground">{s.label}</p>
                <p className={`text-2xl font-bold ${ok ? "" : "text-red-500"}`}>
                  {s.value}
                  <span className="text-sm font-normal text-muted-foreground ml-1">{s.unit}</span>
                </p>
                <p className="text-xs text-muted-foreground">
                  正常范围：{s.min}–{s.max}{s.unit}
                </p>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* 历史记录 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">最近记录</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-muted-foreground">
                  <th className="text-left py-2 pr-4">时间</th>
                  <th className="text-right py-2 px-4">温度(°C)</th>
                  <th className="text-right py-2 px-4">湿度(%)</th>
                  <th className="text-right py-2 px-4">土壤水分(%)</th>
                  <th className="text-right py-2 px-4">CO₂(ppm)</th>
                  <th className="text-right py-2 pl-4">光照(lux)</th>
                </tr>
              </thead>
              <tbody>
                {history.map((row, i) => (
                  <tr key={i} className="border-b last:border-0 hover:bg-muted/50">
                    <td className="py-2 pr-4 text-muted-foreground font-mono text-xs">{row.timestamp}</td>
                    <td className="py-2 px-4 text-right">{row.temperature}</td>
                    <td className="py-2 px-4 text-right">{row.humidity}</td>
                    <td className="py-2 px-4 text-right">{row.soil_moisture}</td>
                    <td className="py-2 px-4 text-right">{row.co2}</td>
                    <td className="py-2 pl-4 text-right">{row.light}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
