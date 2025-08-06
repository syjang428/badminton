from tensorflow.keras.models import load_model
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow import keras
import random
import numpy as np
import os
import matplotlib.pyplot as plt

# ✅ 시드 고정 함수
def set_seed(seed=42):
    np.random.seed(seed)
    tf.random.set_seed(seed)
    random.seed(seed)
    os.environ['TF_DETERMINISTIC_OPS'] = "1"
    os.environ['TF_CUDNN_DETERMINISM'] = "1"
    os.environ['PYTHONHASHSEED'] = str(seed)

set_seed()
model = load_model('leftover_prediction_model.keras')

print(model.summary())

# ✅ 데이터 불러오기 (업로드한 파일 반영)
file_path = '2025_급식데이터_YOLO용_면적단위 (2).csv'
data = pd.read_csv(file_path, encoding='utf-8')

# 공백 제거
data.columns = data.columns.str.strip()

# 열 이름 확인 (디버깅용)
print("열 이름:", data.columns.tolist())

# ✅ 독립변수/종속변수 분리
X = data[['선호도', '기온(°C)', '계절',
          '1학년_남', '1학년_여',
          '2학년_남', '2학년_여',
          '3학년_남', '3학년_여',
          '체육대회', '현장체험학습', '점심행사',
          '제공량(kg)']]

y = data[['잔반량(cm^2)']]

# ✅ 범주형 변수 원핫 인코딩
X_encoded = pd.get_dummies(X, columns=['계절', '점심행사'])

# ✅ 수치형 변수 정규화

scaler = StandardScaler()
num_cols = ['선호도', '기온(°C)', '1학년_남', '1학년_여', '2학년_남', '2학년_여', '3학년_남', '3학년_여', '제공량(kg)']
X_encoded[num_cols] = scaler.fit_transform(X_encoded[num_cols])

# ✅ 새 데이터 예측 예시
new_input = pd.DataFrame([{
    '제공량(kg)': 6.33,
    '선호도': 4,
    '기온(°C)': 12.9,
    '계절': '봄',
    '1학년_남': 28,
    '1학년_여': 21,
    '2학년_남': 29,
    '2학년_여': 28,
    '3학년_남': 27,
    '3학년_여': 30,
    '체육대회': 0,
    '현장체험학습': 0,
    '점심행사': 1
}])


# 새 데이터 전처리
new_encoded = pd.get_dummies(new_input, columns=['계절', '점심행사'])
new_encoded = new_encoded.reindex(columns=X_encoded.columns, fill_value=0)
print(new_encoded)
new_encoded[num_cols] = scaler.transform(new_encoded[num_cols])

# 예측
predicted_leftover = model.predict(new_encoded)
print("예측된 잔반량:", predicted_leftover[0][0])