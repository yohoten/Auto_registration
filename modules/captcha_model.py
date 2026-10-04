import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models
import numpy as np
import os

class CaptchaCNNModel:
    def __init__(self, model_path='models/captcha_cnn.h5'):
        self.model_path = model_path
        self.model = None
        self.img_height = 50
        self.img_width = 120
        self.characters = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        self.max_length = 6
        
    def build_model(self):
        """构建CNN模型"""
        input_layer = keras.Input(shape=(self.img_height, self.img_width, 1))
        
        # 卷积层
        x = layers.Conv2D(32, (3, 3), activation='relu')(input_layer)
        x = layers.MaxPooling2D((2, 2))(x)
        x = layers.Conv2D(64, (3, 3), activation='relu')(x)
        x = layers.MaxPooling2D((2, 2))(x)
        x = layers.Conv2D(64, (3, 3), activation='relu')(x)
        
        # 展平
        x = layers.Flatten()(x)
        x = layers.Dense(128, activation='relu')(x)
        x = layers.Dropout(0.5)(x)
        
        # 多个输出层（每个字符一个输出）
        outputs = []
        for i in range(self.max_length):
            output = layers.Dense(len(self.characters) + 1, activation='softmax', name=f'char_{i}')(x)
            outputs.append(output)
        
        self.model = keras.Model(inputs=input_layer, outputs=outputs)
        
        # 编译模型
        self.model.compile(
            optimizer='adam',
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        return self.model
    
    def train(self, X_train, y_train, X_val=None, y_val=None, epochs=50, batch_size=32):
        """训练模型"""
        if self.model is None:
            self.build_model()
        
        # 准备验证数据
        validation_data = None
        if X_val is not None and y_val is not None:
            # y_val需要拆分为多个输出
            y_val_split = self._split_labels(y_val)
            validation_data = (X_val, y_val_split)
        
        # y_train需要拆分为多个输出
        y_train_split = self._split_labels(y_train)
        
        # 添加回调
        callbacks = [
            keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True),
            keras.callbacks.ModelCheckpoint(
                self.model_path,
                save_best_only=True,
                monitor='val_loss'
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-6
            )
        ]
        
        # 训练模型
        history = self.model.fit(
            X_train, y_train_split,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=validation_data,
            callbacks=callbacks
        )
        
        return history
    
    def _split_labels(self, labels):
        """将标签拆分为多个输出"""
        # labels形状: (samples, max_length, num_chars+1)
        # 拆分为: [ (samples, num_chars+1) for each position ]
        split_labels = []
        for i in range(self.max_length):
            split_labels.append(labels[:, i, :])
        return split_labels
    
    def predict(self, image):
        """预测验证码"""
        if self.model is None:
            self.model = keras.models.load_model(self.model_path)
        
        # 预处理图像
        processed = self._preprocess_image(image)
        
        # 预测
        predictions = self.model.predict(processed)
        
        # 解码预测结果
        captcha_text = self._decode_predictions(predictions)
        
        return captcha_text
    
    def _preprocess_image(self, image):
        """预处理单张图像"""
        from PIL import Image
        import cv2
        
        # 转换为灰度图
        if image.mode != 'L':
            image = image.convert('L')
        
        # 转换为numpy数组
        img_array = np.array(image)
        
        # 二值化
        _, binary = cv2.threshold(img_array, 127, 255, cv2.THRESH_BINARY)
        
        # 调整大小
        resized = cv2.resize(binary, (self.img_width, self.img_height))
        
        # 归一化并添加维度
        normalized = resized / 255.0
        processed = normalized.reshape(1, self.img_height, self.img_width, 1)
        
        return processed
    
    def _decode_predictions(self, predictions):
        """解码预测结果"""
        captcha = ''
        for i in range(self.max_length):
            pred = predictions[i][0]  # 获取第i个字符的预测
            char_idx = np.argmax(pred)
            
            # 如果预测的不是空白符
            if char_idx < len(self.characters):
                captcha += self.characters[char_idx]
        
        return captcha