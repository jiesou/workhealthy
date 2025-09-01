from dataclasses import dataclass, field
import os
import traceback
from backend.detector import BaseDetectionResult, DetectionBox


# 导入 Roboflow Inference
try:
    print("[WorkLabel] 尝试导入 Roboflow Inference 模块...")
    from inference import get_model
    from inference.models.owlv2.owlv2 import OwlV2
    from inference.core.entities.requests.owlv2 import OwlV2InferenceRequest
except ImportError:
    print("[WorkLabel] 警告: 无法导入 inference，工牌检测功能可能不可用")


class WorkLabel:
    """负责检测有没有佩戴工牌，并提供框框"""
    @dataclass
    class WorkLabelResult(BaseDetectionResult):
        has_work_label: bool = False

    def __init__(self):
        """初始化工牌检测器"""
        self.result = self.WorkLabelResult()
        try:
            # 确保环境变量中有 API key
            if not os.getenv('ROBOFLOW_API_KEY'):
                print("[WorkLabel] 未设置 ROBOFLOW_API_KEY 环境变量，工牌检测功能将不可用")
                return

            # 加载您的私有模型
            self.model = get_model(model_id="jiesou/-hdl2k-instant-2")
            print("[WorkLabel] Roboflow 工牌检测模型加载成功")
        except KeyError as e:
            print(f"[WorkLabel] Roboflow 模型类型不支持: {e}")
            print("[WorkLabel] 提示：是否安装了 inference[transformers]？")
            self.model = None
        except Exception as e:
            print(f"[WorkLabel] 加载 Roboflow 模型出错: {e}，工牌检测功能将不可用")

    def detect(self, frame) -> WorkLabelResult:
        """检测图像中的工牌，并返回结果（包含 box）"""
        result = self.WorkLabelResult()

        if self.model is None:
            self.result = result
            return result

        try:
            # 使用 Roboflow 模型进行推理
            results = self.model.infer(frame)[0]
            print(f"[WorkLabel] 检测到 {len(results.predictions)} 个工牌候选")
            # 处理检测结果
            if hasattr(results, 'predictions') and results.predictions:
                for prediction in results.predictions:
                    # 检查置信度阈值
                    if prediction.confidence < 0.5:
                        continue

                    # 标记检测到工牌
                    result.has_work_label = True

                    # 添加检测框
                    result.boxes.append(DetectionBox(
                        x1=int(prediction.x - prediction.width / 2),
                        y1=int(prediction.y - prediction.height / 2),
                        x2=int(prediction.x + prediction.width / 2),
                        y2=int(prediction.y + prediction.height / 2),
                        confidence=prediction.confidence * 100,
                        class_id=prediction.class_id if hasattr(
                            prediction, 'class_id') else 0,
                        class_name=prediction.class_name if hasattr(
                            prediction, 'class_name') else "work_label"
                    ))

                    print(
                        f"[WorkLabel] 检测到工牌: confidence={prediction.confidence:.3f}")

        except Exception as e:
            print(f"[WorkLabel] 工牌检测出错: {e}")
            traceback.print_exc()

        self.result = result
        return result
