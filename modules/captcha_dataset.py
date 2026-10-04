import os
import cv2
import numpy as np
from PIL import Image
import pickle
from sklearn.model_selection import train_test_split
import time

class CaptchaDataset:
    def __init__(self, data_dir='data/captcha'):
        self.data_dir = data_dir
        self.images = []
        self.labels = []
        self.characters = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.char_to_index = {char: idx for idx, char in enumerate(self.characters)}
        self.index_to_char = {idx: char for idx, char in enumerate(self.characters)}
        
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, 'raw'), exist_ok=True)
    
    def load_existing_dataset(self):
        """加载现有数据集"""
        dataset_path = os.path.join(self.data_dir, 'dataset.pkl')
        if os.path.exists(dataset_path):
            with open(dataset_path, 'rb') as f:
                data = pickle.load(f)
                self.images = data['images']
                self.labels = data['labels']
            return True
        return False
    
    def add_captcha(self, image, label):
        """添加验证码样本"""
        # 预处理图像
        processed_img = self._preprocess_image(image)
        
        # 转换标签为one-hot编码
        label_vector = self._encode_label(label)
        
        self.images.append(processed_img)
        self.labels.append(label_vector)
        
        # 保存样本
        timestamp = int(time.time() * 1000)
        filename = f"{label}_{timestamp}.png"
        image.save(os.path.join(self.data_dir, 'raw', filename))
    
    def _preprocess_image(self, image):
        """图像预处理"""
        # 转换为灰度图
        if image.mode != 'L':
            image = image.convert('L')
        
        # 二值化
        img_array = np.array(image)
        _, binary = cv2.threshold(img_array, 127, 255, cv2.THRESH_BINARY)
        
        # 去除噪点
        kernel = np.ones((2, 2), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # 调整大小
        resized = cv2.resize(cleaned, (120, 50))
        
        # 归一化
        normalized = resized / 255.0
        
        return normalized
    
    def _encode_label(self, label):
        """编码标签"""
        # 假设验证码长度为4-6个字符
        max_length = 6
        encoded = []
        
        for i in range(max_length):
            if i < len(label):
                char = label[i]
                if char in self.char_to_index:
                    char_vec = np.zeros(len(self.characters) + 1)  # +1 for blank
                    char_vec[self.char_to_index[char]] = 1
                else:
                    # 未知字符
                    char_vec = np.zeros(len(self.characters) + 1)
                    char_vec[-1] = 1  # 空白符
            else:
                # 空白符
                char_vec = np.zeros(len(self.characters) + 1)
                char_vec[-1] = 1
            
            encoded.append(char_vec)
        
        return np.array(encoded)
    
    def split_dataset(self, test_size=0.2):
        """划分训练集和测试集"""
        X_train, X_test, y_train, y_test = train_test_split(
            self.images, self.labels, test_size=test_size, random_state=42
        )
        
        return X_train, X_test, y_train, y_test
    
    def save_dataset(self):
        """保存数据集"""
        dataset_path = os.path.join(self.data_dir, 'dataset.pkl')
        with open(dataset_path, 'wb') as f:
            pickle.dump({
                'images': self.images,
                'labels': self.labels,
                'characters': self.characters
            }, f)