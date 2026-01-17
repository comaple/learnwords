# WordMem - 智能单词记忆神器开发规划

## 📋 项目概述

### 项目名称
**WordMem** - 基于人类记忆曲线的智能单词记忆神器

### 核心特色
- **📸 便捷录入**: 支持照片和PDF两种方式导入单词
- **🧠 科学记忆**: 基于艾宾浩斯遗忘曲线的个性化记忆系统
- **🤖 智能OCR**: 集成开源免费VLM模型，精准识别文档中的英文单词
- **🎮 趣味学习**: 游戏化设计，让背单词不再枯燥
- **📊 数据分析**: 详细的学习数据统计和效果分析

### 目标用户
- **学生群体**: 初高中学生、大学生
- **职场人士**: 需要提升英语词汇的职场人士
- **语言学习者**: 英语学习爱好者

## 🛠 技术架构方案

### 技术选型分析

#### 前端技术选择

**桌面端: Tauri (推荐)**
- **优势对比**:
  - 安装包体积: 3-10MB vs Electron的100-250MB
  - 内存占用: 30-180MB vs Electron的120-400MB
  - 启动速度: <300ms vs Electron的800-1200ms
  - 安全性: Rust沙箱机制，内存安全
  - 性能: 接近原生应用体验

**移动端: React Native**
- **选择理由**:
  - 单一代码库，iOS优化
  - 成熟生态，社区活跃
  - 性能优秀，接近原生
  - 热更新支持

#### 后端技术选择

**框架: FastAPI**
- **核心优势**:
  - 现代异步框架，性能卓越
  - 自动API文档生成
  - 基于Pydantic的数据验证
  - 类型提示支持
  - 性能测试显示比Flask快2-3倍

#### OCR技术选择

**首选: Gemini Vision (via HTTP API)**
- **技术亮点**:
  - 使用大型多模态模型的视觉能力进行文本与文档识别
  - 可通过托管API调用（低运维成本）
  - 易于与后端异步服务集成，适配多语言和复杂布局

**备注 - 密钥管理**: 请不要将真实 API key 写入版本库。使用环境变量 `GEMINI_API_KEY` 和 `GEMINI_OCR_ENDPOINT`，或使用受控的机密管理服务（Vault、Secrets Manager）。提供的密钥应仅在本地 `.env` 或 CI secret 中使用。

### 系统架构图

```
┌─────────────────┐    ┌─────────────────┐
│   桌面端        │    │   iOS移动端     │
│   (Tauri)       │    │ (React Native)  │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────┬───────┘
                         │
                ┌─────────────────┐
                │   API网关       │
                │   (Nginx)       │
                └─────────────────┘
                         │
                ┌─────────────────┐
                │   FastAPI后端   │
                │   (Python)      │
                └─────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ PaddleOCR-VL    │ │   PostgreSQL    │ │     Redis       │
│   (OCR服务)      │ │   (主数据库)     │ │   (缓存)        │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## 📱 核心功能模块

### 1. 文档导入模块

#### 功能特性
- **照片导入**: 支持JPG/PNG/WebP格式
- **PDF导入**: 支持多页PDF文档解析
- **批量处理**: 多文件同时上传和处理
- **预处理**: 自动图片优化、方向校正、质量压缩

#### 技术实现
```python
# 文件预处理服务
class DocumentPreprocessor:
  def preprocess_image(self, image_path: str) -> ProcessedImage:
    """图片预处理"""
    # 1. 方向检测和校正
    # 2. 质量压缩
    # 3. 格式标准化
    pass
    
  def extract_pdf_pages(self, pdf_path: str) -> List[str]:
    """PDF页面提取"""
    pass
```

#### OCR识别模块

#### 核心能力
- **智能识别**: 文本+表格+公式识别（由 Gemini Vision 提供多模态识别能力）
- **语言检测**: 自动识别文档语言
- **结果优化**: 智能过滤和清洗英文单词
- **编辑功能**: 用户可修正识别结果

#### 技术实现（示例）
```python
import os
import requests
import re
from typing import List, Dict

class OCRService:
  """通过外部 Gemini Vision API 执行 OCR 的示例实现。

  要点:
  - 直接使用 `GEMINI_API_KEY` 调用 Google Generative API（或官方 Gemini 客户端），无需单独配置 OCR endpoint。
  - 可通过环境变量 `GEMINI_MODEL` 指定使用的模型（默认 `gemini-image-1`）。
  - 不要将真实密钥提交到版本库；在本地使用 `.env` 或 CI secrets。
  """

  def __init__(self):
    self.endpoint = os.getenv('GEMINI_OCR_ENDPOINT', '')
    self.api_key = os.getenv('GEMINI_API_KEY', '')
    if not self.endpoint or not self.api_key:
      raise RuntimeError('GEMINI_OCR_ENDPOINT and GEMINI_API_KEY must be set')

  def _call_gemini(self, image_path: str) -> Dict:
    """将图像文件以 multipart/form-data 上传到 Gemini OCR endpoint 并返回 JSON 响应。"""
    headers = {
      'Authorization': f'Bearer {self.api_key}'
    }
    with open(image_path, 'rb') as f:
      files = {'file': (os.path.basename(image_path), f, 'application/octet-stream')}
      resp = requests.post(self.endpoint, headers=headers, files=files, timeout=60)
    resp.raise_for_status()
    return resp.json()

  def process_document(self, file_path: str) -> Dict:
    result = self._call_gemini(file_path)
    # 假设返回结构包含 OCR 文本字段 'text'，请根据实际 API 调整解析逻辑
    raw_text = result.get('text', '')
    words = re.findall(r"\b[A-Za-z]+\b", raw_text)
    english_words = list({w.lower() for w in words if len(w) > 2})
    return {
      'raw_result': result,
      'words': english_words,
      'count': len(english_words),
    }
```

### 3. 智能记忆算法

#### 算法原理
- **艾宾浩斯曲线**: 标准5分钟→30分钟→12小时→1天→2天→4天→7天→15天间隔
- **个性化调整**: 基于用户表现动态调整复习间隔
- **遗忘预测**: LSTM模型预测单词遗忘概率
- **智能提醒**: 基于最佳复习时间推送通知

#### 技术实现
```python
class EbbinghausAlgorithm:
    def __init__(self):
        self.base_intervals = [0.083, 0.5, 12, 24, 48, 96, 168, 360]
    
    def calculate_next_review(
        self, 
        review_count: int, 
        performance: float,
        user_difficulty: float = 1.0
    ) -> datetime:
        """计算下次复习时间"""
        base_interval = self.base_intervals[min(review_count, len(self.base_intervals)-1)]
        
        # 根据表现调整间隔
        if performance >= 0.8:
            adjusted_interval = base_interval * 1.3
        elif performance >= 0.6:
            adjusted_interval = base_interval
        else:
            adjusted_interval = base_interval * 0.7
        
        # 根据个人难度调整
        difficulty_factor = 1 + (user_difficulty - 3) * 0.2
        adjusted_interval *= difficulty_factor
        
        next_review = datetime.now() + timedelta(hours=adjusted_interval)
        return next_review
    
    def predict_forgetting_probability(
        self, 
        word: str, 
        days_since_last_review: int
    ) -> float:
        """预测遗忘概率"""
        # LSTM模型预测
        pass
```

### 4. 游戏化学习系统

#### 核心要素
- **积分系统**: 学习行为获得积分奖励
- **等级机制**: 积分积累提升等级，解锁新功能
- **成就徽章**: 完成特定目标获得成就奖励
- **学习统计**: 详细的数据可视化和进度追踪

#### 游戏化设计
```python
class GamificationService:
    def calculate_learning_points(
        self, 
        action: str, 
        performance: float, 
        streak_days: int
    ) -> int:
        """计算学习积分"""
        base_points = {
            'new_word': 10,
            'review_word': 5,
            'correct_answer': 3,
            'daily_login': 20,
            'streak_bonus': 50
        }
        
        points = base_points.get(action, 0)
        
        # 连续学习加成
        if streak_days > 7:
            points *= 1.2
        
        # 表现加成
        if performance >= 0.9:
            points *= 1.1
        
        return int(points)
    
    def check_achievements(self, user_stats: UserStats) -> List[Achievement]:
        """检查成就解锁"""
        achievements = []
        
        # 单词收集者成就
        if user_stats.total_words_learned >= 100:
            achievements.append(
                Achievement(id='word_collector', name='单词收集者')
            )
        
        # 连续学习大师
        if user_stats.current_streak >= 30:
            achievements.append(
                Achievement(id='streak_master', name='连续学习大师')
            )
        
        return achievements
```

## 📋 详细开发计划

### 第一阶段：基础架构搭建 (2-3周)

#### Week 1: 项目初始化
**后端任务**
- [x] FastAPI项目初始化
- [x] PostgreSQL数据库设计和创建
- [x] Redis缓存配置
- [x] PaddleOCR-VL环境部署
- [x] Docker容器化配置

**前端任务**
- [x] Tauri桌面端项目初始化
- [x] React + TypeScript环境搭建
- [x] 基础UI框架选择和配置
- [x] 路由和状态管理设置

#### Week 2-3: 核心服务开发
**后端任务**
- [ ] 文件上传和预处理服务
- [ ] OCR识别服务集成
- [ ] 用户管理系统
- [ ] 基础API接口开发

**前端任务**
- [ ] 文件上传界面开发
- [ ] OCR结果展示界面
- [ ] 用户登录注册界面
- [ ] 基础导航和布局

### 第二阶段：核心功能实现 (3-4周)

#### Week 4-5: 文档处理功能
**功能开发**
- [ ] 照片导入和批量处理
- [ ] PDF文档解析
- [ ] OCR识别结果展示
- [ ] 单词提取和编辑功能

**技术实现**
- [ ] 图片预处理优化
- [ ] OCR识别准确率调优
- [ ] 大文件处理性能优化
- [ ] 错误处理和重试机制

#### Week 6-7: 学习系统开发
**功能开发**
- [ ] 单词学习界面
- [ ] 艾宾浩斯算法实现
- [ ] 复习提醒系统
- [ ] 学习进度追踪

**技术实现**
- [ ] 记忆算法核心逻辑
- [ ] 个性化调整机制
- [ ] 学习数据统计
- [ ] 推送通知服务

### 第三阶段：记忆算法优化 (2-3周)

#### Week 8-9: 算法完善
**算法优化**
- [ ] 艾宾浩斯算法调优
- [ ] 遗忘预测模型训练
- [ ] 个性化推荐系统
- [ ] 学习效果评估

**数据分析**
- [ ] 用户学习数据收集
- [ ] 算法效果评估
- [ ] A/B测试设计
- [ ] 性能监控和分析

#### Week 10: 测试和优化
**测试工作**
- [ ] 单元测试编写
- [ ] 集成测试
- [ ] 性能测试
- [ ] 用户测试和反馈收集

**优化工作**
- [ ] 代码优化和重构
- [ ] 界面优化
- [ ] 性能调优
- [ ] Bug修复

### 第四阶段：游戏化和iOS端 (5-6周)

#### Week 11-12: 游戏化系统
**功能开发**
- [ ] 积分和等级系统
- [ ] 成就徽章系统
- [ ] 学习统计可视化
- [ ] 社交分享功能

**技术实现**
- [ ] 游戏化后端服务
- [ ] 动画和交互效果
- [ ] 数据可视化图表
- [ ] 分享接口开发

#### Week 13-16: iOS端开发
**React Native开发**
- [ ] React Native项目搭建
- [ ] API接口适配
- [ ] 核心功能移植
- [ ] iOS原生功能集成

**测试和发布**
- [ ] iOS真机测试
- [ ] 性能优化
- [ ] TestFlight内测
- [ ] App Store发布准备

## 🔧 技术实现细节

### 后端核心代码

#### FastAPI主应用
```python
from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

app = FastAPI(
    title="WordMem API",
    description="智能单词记忆神器后端服务",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据库依赖
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API路由
@app.post("/api/v1/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """文件上传和OCR处理"""
    pass

@app.get("/api/v1/learning/plan/{user_id}")
async def get_learning_plan(user_id: str, db: Session = Depends(get_db)):
    """获取学习计划"""
    pass
```

#### OCR服务实现
```python
import asyncio
from typing import List, Dict
from paddleocr import PaddleOCR

class OCRService:
    def __init__(self):
        self.ocr = PaddleOCR(
            use_doc_parser=True,
            lang='en',
            show_log=False,
            use_gpu=True
        )
    
    async def process_image_async(self, image_path: str) -> Dict:
        """异步处理图片"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.ocr, image_path)
        
        # 提取英文单词
        english_words = self._extract_english_words(result)
        
        return {
            "status": "success",
            "words": english_words,
            "count": len(english_words),
            "raw_result": result
        }
    
    def _extract_english_words(self, ocr_result: List) -> List[str]:
        """提取英文单词"""
        english_words = []
        
        for line in ocr_result:
            if len(line) > 0:
                text = line[1][0]  # 获取识别文本
                # 使用正则表达式提取英文单词
                words = re.findall(r'\b[A-Za-z]+\b', text)
                english_words.extend(words)
        
        # 去重并过滤
        return list(set([word.lower() for word in english_words if len(word) > 2]))
```

#### 记忆算法服务
```python
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class MemoryService:
    def __init__(self):
        self.base_intervals = [0.083, 0.5, 12, 24, 48, 96, 168, 360]  # 小时
        
    def calculate_review_schedule(
        self, 
        user_id: str, 
        word_id: str,
        current_performance: float
    ) -> Dict:
        """计算复习计划"""
        # 获取用户学习记录
        user_word = self._get_user_word(user_id, word_id)
        
        if user_word is None:
            # 新单词，立即学习
            return {
                "next_review": datetime.now(),
                "interval": 0,
                "status": "new"
            }
        
        review_count = user_word.review_count
        base_interval = self.base_intervals[min(review_count, len(self.base_intervals)-1)]
        
        # 根据表现调整
        adjusted_interval = self._adjust_interval(base_interval, current_performance)
        
        next_review = datetime.now() + timedelta(hours=adjusted_interval)
        
        return {
            "next_review": next_review,
            "interval": adjusted_interval,
            "status": "reviewing"
        }
    
    def _adjust_interval(self, base_interval: float, performance: float) -> float:
        """根据表现调整间隔"""
        if performance >= 0.8:
            return base_interval * 1.3
        elif performance >= 0.6:
            return base_interval
        else:
            return base_interval * 0.7
```

### 前端核心代码

#### Tauri后端命令
```rust
// src-tauri/src/commands.rs
use serde::{Deserialize, Serialize};
use tauri::command;

#[derive(Debug, Serialize, Deserialize)]
pub struct UploadResponse {
    pub success: bool,
    pub words: Vec<String>,
    pub count: usize,
}

#[command]
async fn upload_file(file_path: String) -> Result<UploadResponse, String> {
    // 调用OCR服务
    match ocr_service::process_image(&file_path).await {
        Ok(result) => Ok(UploadResponse {
            success: true,
            words: result.words,
            count: result.count,
        }),
        Err(e) => Err(e.to_string()),
    }
}

#[command]
async fn get_learning_plan(user_id: String) -> Result<String, String> {
    match learning_service::get_plan(&user_id).await {
        Ok(plan) => Ok(serde_json::to_string(&plan).unwrap()),
        Err(e) => Err(e.to_string()),
    }
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            upload_file,
            get_learning_plan
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

#### React前端组件
```typescript
// src/components/WordCard.tsx
import React, { useState } from 'react';
import { Card, Button, Progress, Tag } from 'antd';
import { invoke } from '@tauri-apps/api/tauri';

interface WordCardProps {
  word: string;
  meaning: string;
  pronunciation?: string;
  difficulty: number;
  onLearn: (word: string) => void;
}

export const WordCard: React.FC<WordCardProps> = ({
  word,
  meaning,
  pronunciation,
  difficulty,
  onLearn
}) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleLearn = async () => {
    setIsLoading(true);
    try {
      await invoke('mark_word_as_learned', { word });
      onLearn(word);
    } catch (error) {
      console.error('学习失败:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getDifficultyColor = (level: number) => {
    if (level <= 2) return 'green';
    if (level <= 3) return 'orange';
    return 'red';
  };

  return (
    <Card
      title={word}
      extra={<Tag color={getDifficultyColor(difficulty)}>{difficulty}</Tag>}
      style={{ marginBottom: 16 }}
    >
      <p>{meaning}</p>
      {pronunciation && <p>发音: {pronunciation}</p>}
      <Button
        type="primary"
        loading={isLoading}
        onClick={handleLearn}
        style={{ marginTop: 8 }}
      >
        开始学习
      </Button>
    </Card>
  );
};
```

#### React Native iOS端
```typescript
// src/services/api.ts
import axios from 'axios';

const API_BASE_URL = 'https://api.wordmem.com/v1';

export const WordMemAPI = {
  uploadFile: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 30000,
    });
    
    return response.data;
  },

  getLearningPlan: async (userId: string) => {
    const response = await axios.get(`${API_BASE_URL}/learning/plan/${userId}`);
    return response.data;
  },

  updateWordProgress: async (userId: string, wordId: string, performance: number) => {
    const response = await axios.post(`${API_BASE_URL}/learning/progress`, {
      userId,
      wordId,
      performance,
    });
    return response.data;
  },
};
```

## 🚀 部署和发布

### 后端部署

#### Docker配置
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/wordmem
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./uploads:/app/uploads

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=wordmem
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api

volumes:
  postgres_data:
  redis_data:
```

### 桌面端发布

#### Tauri配置
```json
// src-tauri/tauri.conf.json
{
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devPath": "http://localhost:3000",
    "distDir": "../dist"
  },
  "package": {
    "productName": "WordMem",
    "version": "1.0.0"
  },
  "tauri": {
    "allowlist": {
      "all": false,
      "fs": {
        "all": true
      },
      "shell": {
        "all": false,
        "open": true
      }
    },
    "bundle": {
      "active": true,
      "targets": "all",
      "identifier": "com.wordmem.app",
      "icon": [
        "icons/32x32.png",
        "icons/128x128.png",
        "icons/128x128@2x.png",
        "icons/icon.icns",
        "icons/icon.ico"
      ]
    }
  }
}
```

### iOS端发布

#### React Native配置
```json
// package.json
{
  "name": "WordMem",
  "version": "1.0.0",
  "scripts": {
    "android": "react-native run-android",
    "ios": "react-native run-ios",
    "start": "react-native start",
    "test": "jest",
    "lint": "eslint . --ext .js,.jsx,.ts,.tsx"
  },
  "dependencies": {
    "react": "18.2.0",
    "react-native": "0.72.0",
    "react-navigation": "^4.4.0",
    "axios": "^1.6.0",
    "react-native-vector-icons": "^10.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.0.0",
    "@types/react-native": "^0.72.0",
    "typescript": "^5.0.0"
  }
}
```

## 📊 项目优势总结

### 技术优势
1. **极致轻量**: Tauri桌面端体积<10MB，内存占用低
2. **高性能**: FastAPI异步处理，OCR识别速度快
3. **开源免费**: PaddleOCR-VL开源，无API调用成本
4. **跨平台**: 统一后端，多端前端共享逻辑

### 功能优势
1. **科学记忆**: 艾宾浩斯曲线 + 个性化智能调整
2. **智能识别**: SOTA级OCR，支持复杂文档和表格
3. **便捷录入**: 照片+PDF双路径，支持批量处理
4. **游戏化学习**: 积分、等级、成就系统提高学习粘性

### 商业优势
1. **零边际成本**: 开源OCR技术，无API费用
2. **快速迭代**: 现代化技术栈，开发效率高
3. **用户友好**: 简洁界面，操作简单
4. **数据驱动**: 详细学习分析，持续优化

### 竞争优势
1. **技术先进**: 2025年最新开源VLM技术
2. **体验优秀**: 跨平台统一体验，性能优异
3. **功能完整**: 从录入到学习到分析全流程覆盖
4. **扩展性强**: 模块化设计，易于功能扩展

## 🎯 成功指标

### 技术指标
- OCR识别准确率: >95%
- 应用启动时间: <3秒
- API响应时间: <500ms
- 系统可用性: >99.9%

### 产品指标
- 用户满意度: >4.5/5.0
- 学习效率提升: >30%
- 用户月留存率: >60%
- 应用商店评分: >4.0

### 业务指标
- 下载量: 上线3个月 >10万
- 日活用户: 上线3个月 >1万
- 用户付费转化: >5%
- 获客成本: <20元

---

**本文档将作为WordMem项目开发的指导性文件，随着项目进展持续更新和完善。**