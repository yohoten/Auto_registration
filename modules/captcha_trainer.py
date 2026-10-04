import threading
import time
from queue import Queue

class CaptchaAutoTrainer:
    def __init__(self, dataset, model):
        self.dataset = dataset
        self.model = model
        self.training_queue = Queue()
        self.is_training = False
        self.min_samples_to_train = 100
        self.retrain_interval = 100  # 每收集100个新样本重新训练
        
    def start_auto_training(self):
        """启动自动训练线程"""
        self.is_training = True
        self.train_thread = threading.Thread(target=self._training_loop)
        self.train_thread.daemon = True
        self.train_thread.start()
    
    def _training_loop(self):
        """训练循环"""
        while self.is_training:
            # 检查是否有足够的新样本
            if len(self.dataset.images) >= self.min_samples_to_train:
                self._train_model()
            
            # 每5分钟检查一次
            time.sleep(300)
    
    def _train_model(self):
        """训练模型"""
        print(f"开始训练模型，样本数量: {len(self.dataset.images)}")
        
        # 划分数据集
        X_train, X_test, y_train, y_test = self.dataset.split_dataset(test_size=0.2)
        
        # 转换数据格式
        X_train = np.array(X_train).reshape(-1, self.model.img_height, self.model.img_width, 1)
        X_test = np.array(X_test).reshape(-1, self.model.img_height, self.model.img_width, 1)
        y_train = np.array(y_train)
        y_test = np.array(y_test)
        
        # 训练模型
        history = self.model.train(
            X_train, y_train,
            X_val=X_test, y_val=y_test,
            epochs=50,
            batch_size=32
        )
        
        # 评估模型
        accuracy = self._evaluate_model(X_test, y_test)
        print(f"模型训练完成，测试集准确率: {accuracy:.2%}")
        
        # 保存数据集
        self.dataset.save_dataset()
    
    def _evaluate_model(self, X_test, y_test):
        """评估模型"""
        # 转换y_test格式
        y_test_split = self.model._split_labels(y_test)
        
        # 评估
        results = self.model.model.evaluate(X_test, y_test_split)
        
        # 返回平均准确率
        accuracy_indices = [i for i, name in enumerate(self.model.model.metrics_names) if 'accuracy' in name]
        avg_accuracy = np.mean([results[i] for i in accuracy_indices])
        
        return avg_accuracy
    
    def add_training_sample(self, image, label):
        """添加训练样本"""
        self.dataset.add_captcha(image, label)
        
        # 检查是否需要重新训练
        if len(self.dataset.images) % self.retrain_interval == 0:
            self._train_model()
    
    def stop_training(self):
        """停止训练"""
        self.is_training = False
        if hasattr(self, 'train_thread'):
            self.train_thread.join(timeout=5)