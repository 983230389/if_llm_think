import os
import sys
import traceback
from dynapyt.analyses.BaseAnalysis import BaseAnalysis


# 绝对暴力的日志写入器，不依赖 stdout
def hard_log(msg):
    with open("dynapyt_hard_debug.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")


class BatchVariableTracker(BaseAnalysis):
    def __init__(self, **kwargs):
        super().__init__()
        self.var_sequences = {}
        hard_log("\n" + "="*40)
        hard_log("🚀 [__init__] 分析模块被成功实例化！")

    def write(self, dyn_ast, iid, *args):
        hard_log(f"🟢 [write] 拦截到变量写入！参数个数: {len(args)}")
        try:
            node = dyn_ast.ast_nodes[iid]

            # 兼容不同版本的 AST 节点提取变量名
            if hasattr(node, "id"):
                var_name = node.id
            elif hasattr(node, "target") and hasattr(node.target, "id"):
                var_name = node.target.id
            else:
                var_name = f"line_{getattr(node, 'lineno', 'unknown')}_var"

            val = args[-1] if args else None

            if var_name not in self.var_sequences:
                self.var_sequences[var_name] = []

            safe_val = val if isinstance(val, (int, float, str, bool)) else str(val)
            self.var_sequences[var_name].append(safe_val)

            hard_log(f"    --> 成功记录: {var_name} = {safe_val}")

        except Exception as e:
            hard_log(f"❌ [write] 提取变量时报错: {e}")
            hard_log(traceback.format_exc())

        return args[-1] if args else None

    def end_execution(self):
        hard_log("🏁 [end_execution] 执行到达结束阶段")
        task_name = os.environ.get("DYNAPYT_TASK_NAME", "manual_test")
        output_dir = os.environ.get("DYNAPYT_OUTPUT_DIR", "original_local")

        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, f"{task_name}.txt")

        hard_log(f"💾 准备将 {len(self.var_sequences)} 个变量写入: {out_path}")

        lines = ["=== 变量变化序列收集结果 ==="]
        for v, seq in self.var_sequences.items():
            lines.append(f"变量 '{v}': {seq}")

        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            hard_log("✅ 文件写入成功！")
        except Exception as e:
            hard_log(f"❌ 写入文件失败: {e}")
            hard_log(traceback.format_exc())