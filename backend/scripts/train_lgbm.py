"""
LightGBM 四任务训练脚本
=======================
从 generate_training_data.py 生成的 JSON 中读取数据，
直接调用 LightGBMDecisionService.fit() 训练并保存模型。

用法:
  cd D:\\1.6\\1.5\\backend
  python scripts/train_lgbm.py

  # 只训练指定任务:
  python scripts/train_lgbm.py --tasks irrigation disease_risk
"""

import argparse
import json
import sys
import time
from pathlib import Path

# 确保从 backend 根目录执行
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.services.lgbm_decision_service import (
    LightGBMDecisionService,
    TASK_CONFIGS,
)

DATA_DIR = Path(__file__).parent / "training_data"
ALL_TASKS = list(TASK_CONFIGS.keys())


def train_task(service: LightGBMDecisionService, task: str) -> dict:
    """训练单个任务，返回结果字典"""
    data_path = DATA_DIR / f"{task}.json"

    if not data_path.exists():
        print(f"  ⚠️  未找到数据文件: {data_path}")
        print(f"     请先运行: python scripts/generate_training_data.py")
        return {}

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    X_train = data["X_train"]
    y_train = data["y_train"]
    X_val   = data.get("X_val")
    y_val   = data.get("y_val")

    print(f"\n{'─'*55}")
    print(f"[DATA] [{task}] 开始训练")
    print(f"   训练集: {len(X_train)} 条 | 验证集: {len(X_val) if X_val else 0} 条")
    print(f"   特征: {TASK_CONFIGS[task]['features']}")
    print(f"   标签: {TASK_CONFIGS[task]['labels']}")

    t0 = time.time()
    result = service.fit(
        task=task,
        X_train=X_train,
        y_train=y_train,
        num_boost_round=150,
        early_stopping_rounds=20,
        X_val=X_val,
        y_val=y_val,
    )
    elapsed = time.time() - t0

    print(f"\n   [OK] 训练完成!")
    print(f"   轮数: {result['n_trees']} | 耗时: {elapsed:.1f}s")
    print(f"   模型保存: {result['model_saved_to']}")

    # 快速验证：用一条测试样本做推理
    test_sample = X_train[0]
    pred = service.predict(task, test_sample)
    print(f"\n   [STAT] 验证推理: [{pred.decision}] confidence={pred.confidence:.3f} | {pred.recommendation}")
    return result


def main():
    parser = argparse.ArgumentParser(description="训练 LightGBM 农业决策模型")
    parser.add_argument(
        "--tasks",
        nargs="+",
        choices=ALL_TASKS,
        default=ALL_TASKS,
        help=f"要训练的任务，默认全部: {ALL_TASKS}",
    )
    parser.add_argument(
        "--model-dir",
        default=None,
        help="模型保存目录，默认 backend/models/lgbm",
    )
    args = parser.parse_args()

    print("=" * 55)
    print("[TRAIN] LightGBM 农业决策模型训练")
    print("=" * 55)
    print(f"任务列表: {args.tasks}")

    service = LightGBMDecisionService(model_save_dir=args.model_dir)

    results = {}
    failed = []
    for task in args.tasks:
        try:
            r = train_task(service, task)
            if r:
                results[task] = r
            else:
                failed.append(task)
        except Exception as e:
            print(f"\n  [FAIL] [{task}] 训练失败: {e}")
            import traceback
            traceback.print_exc()
            failed.append(task)

    # 汇总
    print(f"\n{'='*55}")
    print("[LIST] 训练汇总")
    print(f"{'='*55}")
    for task, r in results.items():
        print(f"  [OK] {task:<20} {r.get('n_trees', '?'):>4} 棵树  {r.get('training_time_ms', 0)/1000:.1f}s")
    if failed:
        print(f"\n  [FAIL] 失败任务: {failed}")

    print(f"\n{'='*55}")
    print("[DONE] 完成！现在可以调用 SmartPipeline 进行 ML 推理了")
    print(f"   模型目录: {service._model_save_dir}")

    # 最终状态报告
    status = service.get_status()
    print("\n[STAT] 模型状态:")
    for task, info in status["tasks"].items():
        marker = "[OK]" if info["is_trained"] else "[ ]"
        print(f"  {marker} {task:<20} trained={info['is_trained']}  saved={info['model_saved']}")


if __name__ == "__main__":
    main()
