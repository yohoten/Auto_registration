import os

# 创建必要的目录结构
directories = [
    'data/captcha/raw',
    'logs',
    'accounts/input',
    'accounts/output',
    'database',
    'models',
    'templates'
]

for directory in directories:
    os.makedirs(directory, exist_ok=True)
    print(f"Created directory: {directory}")

print("Directory setup completed.")