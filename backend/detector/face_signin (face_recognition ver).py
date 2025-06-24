from dataclasses import dataclass, field
import os, pickle
import face_recognition
from backend.video_processor import BaseDetectionResult

NEW_FACE_IMAGES_DIR = "backend/new_face_images"
ENCODINGS_PATH = "backend/facedata_encodings.pkl"

class FaceSignin:
    KNOWN_ENCODINGS = None
    KNOWN_NAMES = None
    """负责检测人脸是谁，并提供框框"""
    @dataclass
    class FaceResult(BaseDetectionResult):
        who: str = "unknown"

    def __init__(self):
        """初始化人脸签到服务，加载人脸特征数据"""
        self.KNOWN_ENCODINGS, self.KNOWN_NAMES = self.load_facedata()
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

    def detect(self, frame)-> FaceResult:
        """
        检测图像中的人脸，并返回结果（包含 box）
        """
        
        if self.model is None:
            return self.result
            
        return self.result

    def signin(self, user_id, image_path):
        # 识别上传图片
        unknown_img = face_recognition.load_image_file(image_path)
        unknown_encodings = face_recognition.face_encodings(unknown_img)
        if not unknown_encodings:
            return {"success": False, "message": "未检测到人脸"}
        unknown_encoding = unknown_encodings[0]

        # 计算所有已知人脸的距离
        distances = face_recognition.face_distance(
            self.KNOWN_ENCODINGS, unknown_encoding)
        min_distance = float(distances.min())
        min_index = int(distances.argmin())

        # 设置更严格的阈值
        THRESHOLD = 0.5
        if min_distance < THRESHOLD:
            name = self.KNOWN_NAMES[min_index]
            return {"success": True, "message": f"欢迎，{name}！签到成功"}
        else:
            return {"success": False, "message": "未识别到已注册人脸"}
