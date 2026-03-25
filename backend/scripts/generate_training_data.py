"""
农业 LightGBM 训练数据生成器
============================
基于农业领域知识合成四个任务的训练数据集：
  1. irrigation       — 灌溉决策
  2. disease_risk     — 病害风险评估
  3. fertilization    — 施肥决策
  4. harvest_timing   — 采收时机预测

每个任务生成 2000 条样本（1500 训练 / 500 验证）。
数据分布遵循真实农业场景：特征间有相关性，边界附近加噪声。
"""

import json
import random
import sys
from pathlib import Path

import numpy as np

np.random.seed(42)
random.seed(42)


# ═══════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════

def noise(val, sigma=0.05):
    """给标量加高斯噪声"""
    return float(val + np.random.normal(0, sigma * max(abs(val), 1)))


def clip(val, lo, hi):
    return float(np.clip(val, lo, hi))


# ═══════════════════════════════════════════════════════
# 任务1：灌溉决策
# ═══════════════════════════════════════════════════════
# features: soil_moisture, temperature, humidity,
#           evapotranspiration, rainfall_24h, forecast_temp, plant_stage
# labels:  0=no_action / 1=irrigate_soon / 2=irrigate_now / 3=urgent_irrigation

def gen_irrigation(n=2000):
    X, y = [], []
    labels_map = {
        0: "no_action",
        1: "irrigate_soon",
        2: "irrigate_now",
        3: "urgent_irrigation",
    }
    # 按比例生成各类样本（稍微不均衡，像真实数据）
    dist = [0.30, 0.30, 0.25, 0.15]
    counts = [int(n * d) for d in dist]
    counts[-1] += n - sum(counts)  # 补足

    for label, cnt in enumerate(counts):
        for _ in range(cnt):
            if label == 0:  # no_action — 土壤湿润
                sm   = clip(np.random.uniform(60, 100), 0, 100)
                temp = clip(np.random.uniform(15, 32), 0, 50)
                hum  = clip(np.random.uniform(40, 80), 0, 100)
                et   = clip(np.random.uniform(1, 3), 0, 20)
                rain = clip(np.random.uniform(5, 30), 0, 100)
                ft   = clip(temp + np.random.uniform(-3, 3), 0, 50)
                ps   = clip(np.random.uniform(0, 1), 0, 1)

            elif label == 1:  # irrigate_soon — 开始偏干
                sm   = clip(np.random.uniform(38, 62), 0, 100)
                temp = clip(np.random.uniform(20, 36), 0, 50)
                hum  = clip(np.random.uniform(30, 65), 0, 100)
                et   = clip(np.random.uniform(2, 5), 0, 20)
                rain = clip(np.random.uniform(0, 5), 0, 100)
                ft   = clip(temp + np.random.uniform(-2, 5), 0, 50)
                ps   = clip(np.random.uniform(0, 1), 0, 1)

            elif label == 2:  # irrigate_now — 明显缺水
                sm   = clip(np.random.uniform(22, 40), 0, 100)
                temp = clip(np.random.uniform(25, 40), 0, 50)
                hum  = clip(np.random.uniform(20, 50), 0, 100)
                et   = clip(np.random.uniform(4, 8), 0, 20)
                rain = clip(np.random.uniform(0, 2), 0, 100)
                ft   = clip(temp + np.random.uniform(0, 6), 0, 50)
                ps   = clip(np.random.uniform(0.3, 1), 0, 1)

            else:             # urgent_irrigation — 严重缺水
                sm   = clip(np.random.uniform(0, 23), 0, 100)
                temp = clip(np.random.uniform(30, 45), 0, 50)
                hum  = clip(np.random.uniform(10, 35), 0, 100)
                et   = clip(np.random.uniform(6, 15), 0, 20)
                rain = clip(np.random.uniform(0, 1), 0, 100)
                ft   = clip(temp + np.random.uniform(1, 8), 0, 50)
                ps   = clip(np.random.uniform(0.5, 1), 0, 1)

            # 加轻微噪声，防止过拟合
            row = {
                "soil_moisture":        noise(sm, 0.02),
                "temperature":          noise(temp, 0.02),
                "humidity":             noise(hum, 0.02),
                "evapotranspiration":   noise(et, 0.05),
                "rainfall_24h":         noise(rain, 0.05),
                "forecast_temp":        noise(ft, 0.02),
                "plant_stage":          noise(ps, 0.01),
            }
            X.append(row)
            y.append(label)

    return X, y


# ═══════════════════════════════════════════════════════
# 任务2：病害风险评估
# ═══════════════════════════════════════════════════════
# features: temperature, humidity, leaf_wetness, rainfall_48h,
#           wind_speed, crop_type_encoded, growth_stage
# labels:  0=low_risk / 1=moderate_risk / 2=high_risk / 3=critical_risk

def gen_disease_risk(n=2000):
    X, y = [], []
    dist = [0.35, 0.30, 0.20, 0.15]
    counts = [int(n * d) for d in dist]
    counts[-1] += n - sum(counts)

    for label, cnt in enumerate(counts):
        for _ in range(cnt):
            if label == 0:  # low_risk
                temp = clip(np.random.uniform(5, 15), 0, 50)  # 冷/热不利病害
                hum  = clip(np.random.uniform(20, 60), 0, 100)
                lw   = clip(np.random.uniform(0, 0.3), 0, 1)
                rain = clip(np.random.uniform(0, 5), 0, 200)
                wind = clip(np.random.uniform(3, 12), 0, 30)
                crop = int(np.random.choice([0, 1, 2, 3]))
                gs   = clip(np.random.uniform(0, 1), 0, 1)

            elif label == 1:  # moderate_risk
                temp = clip(np.random.uniform(18, 28), 0, 50)
                hum  = clip(np.random.uniform(55, 75), 0, 100)
                lw   = clip(np.random.uniform(0.1, 0.5), 0, 1)
                rain = clip(np.random.uniform(2, 15), 0, 200)
                wind = clip(np.random.uniform(1, 8), 0, 30)
                crop = int(np.random.choice([0, 1, 2, 3]))
                gs   = clip(np.random.uniform(0.2, 0.8), 0, 1)

            elif label == 2:  # high_risk
                temp = clip(np.random.uniform(20, 30), 0, 50)
                hum  = clip(np.random.uniform(75, 90), 0, 100)
                lw   = clip(np.random.uniform(0.4, 0.8), 0, 1)
                rain = clip(np.random.uniform(10, 40), 0, 200)
                wind = clip(np.random.uniform(0, 4), 0, 30)
                crop = int(np.random.choice([0, 1, 2, 3]))
                gs   = clip(np.random.uniform(0.3, 1.0), 0, 1)

            else:             # critical_risk — 温湿度完美配合
                temp = clip(np.random.uniform(22, 28), 0, 50)
                hum  = clip(np.random.uniform(88, 100), 0, 100)
                lw   = clip(np.random.uniform(0.7, 1.0), 0, 1)
                rain = clip(np.random.uniform(20, 80), 0, 200)
                wind = clip(np.random.uniform(0, 2), 0, 30)
                crop = int(np.random.choice([1, 2]))  # 易感作物
                gs   = clip(np.random.uniform(0.4, 1.0), 0, 1)

            row = {
                "temperature":          noise(temp, 0.02),
                "humidity":             noise(hum, 0.02),
                "leaf_wetness":         noise(lw, 0.03),
                "rainfall_48h":         noise(rain, 0.05),
                "wind_speed":           noise(wind, 0.05),
                "crop_type_encoded":    float(crop),
                "growth_stage":         noise(gs, 0.02),
            }
            X.append(row)
            y.append(label)

    return X, y


# ═══════════════════════════════════════════════════════
# 任务3：施肥决策
# ═══════════════════════════════════════════════════════
# features: soil_n, soil_p, soil_k, soil_ph, ec,
#           crop_type_encoded, growth_stage, last_fertilize_days
# labels:  0=no_need / 1=light_fertilize / 2=standard_fertilize / 3=heavy_fertilize

def gen_fertilization(n=2000):
    X, y = [], []
    dist = [0.25, 0.30, 0.30, 0.15]
    counts = [int(n * d) for d in dist]
    counts[-1] += n - sum(counts)

    for label, cnt in enumerate(counts):
        for _ in range(cnt):
            if label == 0:  # no_need — 养分充足
                n_  = clip(np.random.uniform(100, 200), 0, 300)
                p_  = clip(np.random.uniform(50, 100), 0, 200)
                k_  = clip(np.random.uniform(80, 160), 0, 300)
                ph  = clip(np.random.uniform(6.0, 7.2), 4, 9)
                ec  = clip(np.random.uniform(0.5, 1.5), 0, 5)
                lfd = clip(np.random.uniform(5, 20), 0, 90)

            elif label == 1:  # light_fertilize
                n_  = clip(np.random.uniform(70, 110), 0, 300)
                p_  = clip(np.random.uniform(35, 55), 0, 200)
                k_  = clip(np.random.uniform(55, 85), 0, 300)
                ph  = clip(np.random.uniform(5.8, 7.5), 4, 9)
                ec  = clip(np.random.uniform(0.3, 1.2), 0, 5)
                lfd = clip(np.random.uniform(10, 30), 0, 90)

            elif label == 2:  # standard_fertilize
                n_  = clip(np.random.uniform(40, 75), 0, 300)
                p_  = clip(np.random.uniform(20, 40), 0, 200)
                k_  = clip(np.random.uniform(30, 60), 0, 300)
                ph  = clip(np.random.uniform(5.5, 8.0), 4, 9)
                ec  = clip(np.random.uniform(0.2, 0.8), 0, 5)
                lfd = clip(np.random.uniform(15, 45), 0, 90)

            else:             # heavy_fertilize — 严重缺肥
                n_  = clip(np.random.uniform(0, 45), 0, 300)
                p_  = clip(np.random.uniform(0, 25), 0, 200)
                k_  = clip(np.random.uniform(0, 35), 0, 300)
                ph  = clip(np.random.uniform(4.5, 6.0), 4, 9)
                ec  = clip(np.random.uniform(0.0, 0.4), 0, 5)
                lfd = clip(np.random.uniform(30, 90), 0, 90)

            crop = int(np.random.choice([0, 1, 2, 3]))
            gs   = clip(np.random.uniform(0, 1), 0, 1)

            row = {
                "soil_n":               noise(n_, 0.03),
                "soil_p":               noise(p_, 0.03),
                "soil_k":               noise(k_, 0.03),
                "soil_ph":              noise(ph, 0.01),
                "ec":                   noise(ec, 0.05),
                "crop_type_encoded":    float(crop),
                "growth_stage":         noise(gs, 0.02),
                "last_fertilize_days":  noise(lfd, 0.02),
            }
            X.append(row)
            y.append(label)

    return X, y


# ═══════════════════════════════════════════════════════
# 任务4：采收时机预测
# ═══════════════════════════════════════════════════════
# features: accumulated_temperature, days_since_flowering,
#           fruit_color_index, sugar_content, firmness,
#           weather_forecast_rain, market_price_index
# labels:  0=too_early / 1=approaching / 2=optimal / 3=overdue

def gen_harvest_timing(n=2000):
    X, y = [], []
    dist = [0.25, 0.30, 0.30, 0.15]
    counts = [int(n * d) for d in dist]
    counts[-1] += n - sum(counts)

    for label, cnt in enumerate(counts):
        for _ in range(cnt):
            if label == 0:  # too_early — 幼果期
                at   = clip(np.random.uniform(200, 600), 0, 2000)
                days = clip(np.random.uniform(0, 50), 0, 150)
                fci  = clip(np.random.uniform(0.0, 0.4), 0, 1)
                sug  = clip(np.random.uniform(3, 8), 0, 30)
                firm = clip(np.random.uniform(8, 12), 0, 15)
                rain = clip(np.random.uniform(0, 50), 0, 100)
                mpi  = clip(np.random.uniform(0.5, 1.5), 0, 3)

            elif label == 1:  # approaching — 接近成熟
                at   = clip(np.random.uniform(600, 900), 0, 2000)
                days = clip(np.random.uniform(50, 75), 0, 150)
                fci  = clip(np.random.uniform(0.35, 0.65), 0, 1)
                sug  = clip(np.random.uniform(8, 14), 0, 30)
                firm = clip(np.random.uniform(6, 9), 0, 15)
                rain = clip(np.random.uniform(0, 30), 0, 100)
                mpi  = clip(np.random.uniform(0.8, 2.0), 0, 3)

            elif label == 2:  # optimal — 最佳采收
                at   = clip(np.random.uniform(900, 1200), 0, 2000)
                days = clip(np.random.uniform(70, 95), 0, 150)
                fci  = clip(np.random.uniform(0.62, 0.90), 0, 1)
                sug  = clip(np.random.uniform(13, 22), 0, 30)
                firm = clip(np.random.uniform(4, 7), 0, 15)
                rain = clip(np.random.uniform(0, 15), 0, 100)
                mpi  = clip(np.random.uniform(1.2, 2.5), 0, 3)

            else:             # overdue — 过熟
                at   = clip(np.random.uniform(1200, 1800), 0, 2000)
                days = clip(np.random.uniform(90, 150), 0, 150)
                fci  = clip(np.random.uniform(0.88, 1.0), 0, 1)
                sug  = clip(np.random.uniform(20, 30), 0, 30)
                firm = clip(np.random.uniform(0, 4), 0, 15)
                rain = clip(np.random.uniform(0, 80), 0, 100)
                mpi  = clip(np.random.uniform(0.3, 1.2), 0, 3)

            row = {
                "accumulated_temperature":  noise(at, 0.02),
                "days_since_flowering":     noise(days, 0.02),
                "fruit_color_index":        noise(fci, 0.02),
                "sugar_content":            noise(sug, 0.03),
                "firmness":                 noise(firm, 0.03),
                "weather_forecast_rain":    noise(rain, 0.05),
                "market_price_index":       noise(mpi, 0.03),
            }
            X.append(row)
            y.append(label)

    return X, y


# ═══════════════════════════════════════════════════════
# 主函数：生成 + 保存
# ═══════════════════════════════════════════════════════

def split_data(X, y, val_ratio=0.25):
    """随机切分训练集和验证集"""
    idx = list(range(len(X)))
    np.random.shuffle(idx)
    split = int(len(idx) * (1 - val_ratio))
    train_idx, val_idx = idx[:split], idx[split:]
    X_train = [X[i] for i in train_idx]
    y_train = [y[i] for i in train_idx]
    X_val   = [X[i] for i in val_idx]
    y_val   = [y[i] for i in val_idx]
    return X_train, y_train, X_val, y_val


def main():
    output_dir = Path(__file__).parent / "training_data"
    output_dir.mkdir(exist_ok=True)

    generators = {
        "irrigation":     gen_irrigation,
        "disease_risk":   gen_disease_risk,
        "fertilization":  gen_fertilization,
        "harvest_timing": gen_harvest_timing,
    }

    label_names = {
        "irrigation":     ["no_action", "irrigate_soon", "irrigate_now", "urgent_irrigation"],
        "disease_risk":   ["low_risk", "moderate_risk", "high_risk", "critical_risk"],
        "fertilization":  ["no_need", "light_fertilize", "standard_fertilize", "heavy_fertilize"],
        "harvest_timing": ["too_early", "approaching", "optimal", "overdue"],
    }

    for task, gen_fn in generators.items():
        print(f"\n{'='*50}")
        print(f"生成 [{task}] 数据集...")
        X, y = gen_fn(n=2000)
        X_train, y_train, X_val, y_val = split_data(X, y)

        # 保存 JSON
        data = {
            "task":     task,
            "n_train":  len(X_train),
            "n_val":    len(X_val),
            "labels":   label_names[task],
            "X_train":  X_train,
            "y_train":  y_train,
            "X_val":    X_val,
            "y_val":    y_val,
        }
        out_path = output_dir / f"{task}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 统计类别分布
        from collections import Counter
        dist = Counter(y_train)
        print(f"  训练集: {len(X_train)} 条 | 验证集: {len(X_val)} 条")
        print(f"  类别分布: { {label_names[task][k]: v for k, v in sorted(dist.items())} }")
        print(f"  已保存: {out_path}")

    print("\n[OK] 全部数据集生成完毕！")
    print(f"   位置: {output_dir}")
    print("\n下一步：运行 train_lgbm.py 训练四个任务")


if __name__ == "__main__":
    main()
