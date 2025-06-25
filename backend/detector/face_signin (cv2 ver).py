from dataclasses import dataclass, field
import os
import pickle
import cv2
import cv2.data
import numpy as np
from backend.detector import BaseDetectionResult, DetectionBox

NEW_FACE_IMAGES_DIR = "backend/new_face_images"
ENCODINGS_PATH = "backend/lbph_facedata_encodings.pkl"


class FaceSignin:
    """负责检测人脸是谁，并提供框框"""
    KNOWN_ENCODINGS = None
    KNOWN_NAMES = None
    @dataclass
    class FaceResult(BaseDetectionResult):
        recognized_who: str = "unknown"

    def __init__(self):
        """初始化人脸签到服务，加载人脸特征数据"""
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.recognizer = cv2.face.LBPHFaceRecognizer.create()
        self.KNOWN_ENCODINGS, self.KNOWN_NAMES = self.load_facedata()
        self.result = self.FaceResult()

    def load_facedata(self):
        """加载人脸库特征到内存，支持特征缓存"""
        if os.path.exists(ENCODINGS_PATH):
            with open(ENCODINGS_PATH, "rb") as f:
                faces, names = pickle.load(f)
                if faces and names:
                    labels = list(range(len(names)))
                    self.recognizer.train(faces, np.array(labels))
                return faces, names

        faces = []
        names = []
        for filename in os.listdir(NEW_FACE_IMAGES_DIR):
            print(f"正在处理人脸图像: {filename}")
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                name = os.path.splitext(filename)[0]
                img_path = os.path.join(NEW_FACE_IMAGES_DIR, filename)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                detected_faces = self.face_cascade.detectMultiScale(
                    img, 1.1, 4)
                if len(detected_faces) > 0:
                    x, y, w, h = detected_faces[0]
                    face_roi = cv2.resize(img[y:y+h, x:x+w], (100, 100))
                    faces.append(face_roi)
                    names.append(name)

        # 保存特征缓存
        if faces:
            labels = list(range(len(names)))
            self.recognizer.train(faces, np.array(labels))
            with open(ENCODINGS_PATH, "wb") as f:
                pickle.dump((faces, names), f)
        return faces, names

    def detect(self, frame) -> FaceResult:
        """检测图像中的人脸，并返回结果（包含 box）"""
        result = self.FaceResult()

        # 预处理
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

        for (x, y, w, h) in faces:
            print(f"[FaceSignin] 检测到人脸: x={x}, y={y}, w={w}, h={h}")
            face_roi = cv2.resize(gray[y:y+h, x:x+w], (100, 100))
            label, confidence = self.recognizer.predict(face_roi)
            print(f"[FaceSignin] 识别结果: label={label}, confidence={confidence}")
            if confidence < 130: # cv2 的 confidence 越低越好，130是一个经验值
                result.recognized_who = self.KNOWN_NAMES[label]
            else:
                result.recognized_who = "unknown"

            result.boxes.append(DetectionBox(
                x1=x, y1=y, x2=x+w, y2=y+h,
                confidence=100-confidence if confidence < 80 else 0,
                class_id=label if confidence < 80 else -1,
                class_name=result.recognized_who
            ))
        
        self.result = result
        return result
