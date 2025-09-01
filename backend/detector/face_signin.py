from dataclasses import dataclass, field
import os
import pickle
import re
import face_recognition
import numpy as np
from backend.detector import BaseDetectionResult, DetectionBox
from backend.detector.work_label import WorkLabel
import multiprocessing

NEW_FACE_IMAGES_DIR = "backend/new_face_images"
ENCODINGS_PATH = "backend/facedata_encodings.pkl"


class FaceSignin:
    KNOWN_ENCODINGS = None
    KNOWN_NAMES = None
    """负责检测人脸是谁，并提供框框。WorkLabel 是它的关键组成部分"""
    @dataclass
    class FaceResult(BaseDetectionResult):
        recognized_who: str = "unknown"
        has_work_label: bool = False

    def __init__(self):
        """初始化人脸签到服务，加载人脸特征数据"""
        self.KNOWN_ENCODINGS, self.KNOWN_NAMES = self.load_facedata()

        self.work_label_detector = WorkLabel()
        self.result = self.FaceResult()

    def load_facedata(self):
        """加载人脸库特征到内存，支持特征缓存"""
        encodings = []
        names = []
        if os.path.exists(ENCODINGS_PATH):
            with open(ENCODINGS_PATH, "rb") as f:
                encodings, names = pickle.load(f)
                return encodings, names

        for filename in os.listdir(NEW_FACE_IMAGES_DIR):
            print(f"正在处理人脸图像: {filename}")
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                name = os.path.splitext(filename)[0]
                img_path = os.path.join(NEW_FACE_IMAGES_DIR, filename)
                img = face_recognition.load_image_file(img_path)
                feats = face_recognition.face_encodings(img)
                if feats:
                    encodings.append(feats[0])
                    names.append(name)
        # 保存特征缓存
        with open(ENCODINGS_PATH, "wb") as f:
            pickle.dump((encodings, names), f)
        return encodings, names

    def detect_faces(self, frame, queue: multiprocessing.Queue):
        """并行执行人脸检测，并返回结果（包含box）"""
        result = self.FaceResult()

        if not self.KNOWN_ENCODINGS:
            queue.put(result)
            return

        # 检测人脸位置和编码
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)
        print(f"[FaceSignin] 检测到 {len(face_locations)} 张人脸")

        for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
            print(
                f"[FaceSignin] 检测到人脸: x={left}, y={top}, w={right-left}, h={bottom-top}")

            # 计算距离
            distances = face_recognition.face_distance(
                self.KNOWN_ENCODINGS, face_encoding)
            min_distance = float(distances.min())
            min_index = int(distances.argmin())

            print(
                f"[FaceSignin] 识别结果: min_distance={min_distance:.3f}, person={self.KNOWN_NAMES[min_index]}")

            # 设置阈值
            THRESHOLD = 0.4
            if min_distance < THRESHOLD:
                result.recognized_who = self.KNOWN_NAMES[min_index]
                confidence = (1 - min_distance) * 100  # 转换为百分比
                class_id = min_index
            else:
                result.recognized_who = "unknown"
                confidence = 0
                class_id = -1

            result.boxes.append(DetectionBox(
                x1=left, y1=top, x2=right, y2=bottom,
                confidence=confidence,
                class_id=class_id,
                class_name=result.recognized_who
            ))

        queue.put(result)

    def detect_work_label(self, frame, queue: multiprocessing.Queue):
        """并行执行工牌检测"""
        work_label_result = self.work_label_detector.detect(frame)
        queue.put(work_label_result)

    def detect(self, frame) -> FaceResult:
        """检测图像中的人脸和工牌，并返回结果（包含 box），使用并行处理"""
        result = self.FaceResult()

        if not self.KNOWN_ENCODINGS:
            return result

        # 使用 multiprocessing.Queue 来传递结果
        queue = multiprocessing.Queue()

        # 创建两个进程：一个用于人脸检测，一个用于工牌检测
        face_process = multiprocessing.Process(target=self.detect_faces, args=(frame, queue))
        work_label_process = multiprocessing.Process(target=self.detect_work_label, args=(frame, queue))

        # 启动进程
        face_process.start()
        work_label_process.start()

        # 等待进程完成
        face_process.join()
        work_label_process.join()

        # 从队列中获取结果
        face_result = queue.get()
        work_label_result = queue.get()

        # 合并结果
        result.recognized_who = face_result.recognized_who
        result.has_work_label = work_label_result.has_work_label
        result.boxes.extend(face_result.boxes)
        result.boxes.extend(work_label_result.boxes)

        self.result = result
        return result