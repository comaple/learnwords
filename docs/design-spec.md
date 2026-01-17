# WordMem - 详细设计文档

版本：1.0
日期：2026-01-17
作者：自动生成

## 1. 概述

WordMem 是一个面向个人学习者的跨平台单词记忆与管理系统，核心功能包括：文档/图片导入、OCR 识别（使用 Gemini 多模态能力）、单词提取与清洗、基于艾宾浩斯记忆曲线的复习计划、游戏化激励系统以及数据统计与分析。

目标：快速将纸质或电子文档中的英文单词提取并生成个性化复习计划，提高用户记忆效率。


## 2. 高层架构

- 前端桌面：Tauri + React（UI、单词展示、文件上传、本地存储小量状态）
- 移动端：React Native（可选）
- 后端 API：FastAPI（业务逻辑、用户管理、复习算法、任务队列接入）
- OCR/视觉理解：直接调用 Gemini（`gemini-image-1` 等模型）进行图像文本提取与结构化理解
- 数据库：PostgreSQL（持久化用户、单词与学习记录）
- 缓存/队列：Redis（会话、任务状态、短期缓存）
- 存储：本地或对象存储（上传的文件）
- 部署：Docker + docker-compose（开发），可扩展到 k8s

组件图（文字版）：

Client(Tauri/React) <---> API (FastAPI) <---> Postgres
                                    |
                                    +--> Redis
                                    |
                                    +--> Gemini (Generative API)
                                    |
                                    +--> Storage (uploads/ or S3)


## 3. 功能分解

1. 用户管理
   - 注册/登录（JWT 或 Session）
   - 个人资料（昵称、邮箱、偏好）
2. 文件上传与预处理
   - 支持：图片（jpg/png/webp）、PDF（多页）
   - 预处理：方向校正、分辨率调整、图片增强
3. OCR 与单词提取
   - 使用 Gemini 识别图片并提取纯文本
   - 文本清洗（去除标点、表格标签等）并抽取英文单词
4. 单词管理
   - 单词条目（词形、词性、释义、音标、例句）
   - 用户词汇库与进度（UserWord）
5. 学习计划与复习
   - 基于艾宾浩斯曲线的间隔复习算法
   - 根据用户表现调整间隔
6. 游戏化
   - 积分、等级、成就、签到奖励
7. 日志与监控
   - 操作日志、错误日志、性能埋点


## 4. API 设计（主要端点）

- POST /api/v1/upload
  - 描述：上传文件（image/pdf），触发 OCR 和单词提取
  - 请求：multipart/form-data { file }
  - 响应：{ upload_id, words: ["word"], count }

- GET /api/v1/ocr/result/{upload_id}
  - 描述：查询 OCR 处理结果
  - 响应：{ upload_id, status, words, raw_result }

- POST /api/v1/users/register
  - 请求：{ email, password, name }
  - 响应：{ user_id, token }

- POST /api/v1/users/login
  - 请求：{ email, password }
  - 响应：{ token }

- GET /api/v1/learning/plan/{user_id}
  - 描述：获取当日/近期复习计划
  - 响应：{ plans: [{ word_id, next_review, interval_hours, status }] }

- POST /api/v1/learning/progress
  - 请求：{ user_id, word_id, performance (0.0-1.0) }
  - 响应：{ next_review, interval_hours }

- GET /api/v1/words/{word_id}
  - 描述：获取单词详情

- POST /api/v1/words/{word_id}/mark_learned
  - 描述：标记单词已学习、增加记录


## 5. 数据模型与数据库表设计（PostgreSQL）

说明：字段类型给出的是建议（Postgres 类型）。索引、约束与关系也一并列出。

1) users
- id: UUID PRIMARY KEY
- email: VARCHAR(255) UNIQUE NOT NULL
- password_hash: VARCHAR(255) NOT NULL
- name: VARCHAR(100)
- created_at: TIMESTAMP WITH TIME ZONE DEFAULT now()
- last_login: TIMESTAMP WITH TIME ZONE

索引：email(unique)

2) uploads
- id: UUID PRIMARY KEY
- user_id: UUID REFERENCES users(id) ON DELETE SET NULL
- filename: TEXT
- storage_path: TEXT
- status: VARCHAR(20) -- pending/processing/done/failed
- created_at: TIMESTAMP DEFAULT now()
- processed_at: TIMESTAMP

索引：user_id, status

3) ocr_results
- id: UUID PRIMARY KEY
- upload_id: UUID REFERENCES uploads(id) ON DELETE CASCADE
- raw_json: JSONB
- plain_text: TEXT
- words_extracted: TEXT[] -- array of lowercased words
- count: INTEGER
- created_at: TIMESTAMP DEFAULT now()

索引：upload_id

4) words
- id: UUID PRIMARY KEY
- lemma: TEXT -- 词形或词干（lowercase）
- pos: VARCHAR(32) -- 可选词性
- definition: TEXT -- 简短释义
- pronunciation: TEXT -- 音标或发音 URL
- example: TEXT -- 示例句
- created_at: TIMESTAMP DEFAULT now()

索引：lemma(unique)

5) user_words
- id: UUID PRIMARY KEY
- user_id: UUID REFERENCES users(id) ON DELETE CASCADE
- word_id: UUID REFERENCES words(id) ON DELETE CASCADE
- added_at: TIMESTAMP DEFAULT now()
- review_count: INTEGER DEFAULT 0
- last_review_at: TIMESTAMP
- next_review_at: TIMESTAMP
- ease_factor: REAL DEFAULT 2.5 -- 可用于 SM-2 类算法
- interval_hours: REAL DEFAULT 0
- performance_history: JSONB -- 历史表现记录数组

索引：user_id, next_review_at (用于查询到期复习)

6) learning_sessions
- id: UUID PRIMARY KEY
- user_id: UUID REFERENCES users(id)
- started_at: TIMESTAMP
- ended_at: TIMESTAMP
- metrics: JSONB -- 如正确率、完成数

7) achievements
- id: UUID PRIMARY KEY
- code: VARCHAR(64) UNIQUE
- name: VARCHAR(128)
- description: TEXT

8) user_achievements
- id: UUID PRIMARY KEY
- user_id: UUID REFERENCES users(id)
- achievement_id: UUID REFERENCES achievements(id)
- awarded_at: TIMESTAMP DEFAULT now()

9) notifications (optional)
- id: UUID PRIMARY KEY
- user_id: UUID REFERENCES users(id)
- type: VARCHAR(32)
- payload: JSONB
- read: BOOLEAN DEFAULT FALSE
- created_at: TIMESTAMP DEFAULT now()


## 6. 字段说明与约束

- 所有 UUID 字段使用 `uuid_generate_v4()` 作为默认值（需要 `pgcrypto` 或 `uuid-ossp` 扩展）。
- 时间统一使用 UTC（TIMESTAMP WITH TIME ZONE）。
- 敏感信息（密码）仅保存哈希（例如 `bcrypt`），切勿保存明文。
- `words_extracted` 使用数组类型并保持小写去重，便于快速匹配。


## 7. 学习计划算法（概要）

- 每个 `user_word` 记录包含 `review_count`, `ease_factor`, `interval_hours`。
- 新单词：立即安排初次学习（interval=0），review_count=0。
- 完成一次复习后：按性能更新 `review_count` 和 `interval_hours`：
  - performance >= 0.8: interval *= 1.3
  - 0.6 <= performance < 0.8: interval *= 1.0
  - performance < 0.6: interval *= 0.7
- 使用 `next_review_at = last_review_at + interval_hours`（以小时为单位）
- 可选：引入 SM-2 或基于模型的预测（LSTM）来优化 `ease_factor`。


## 8. 实现细节与流程说明

1. 上传流程
   - 用户上传文件到 `/api/v1/upload`。
   - 后端将文件存储到 `uploads/`（或对象存储），创建 `uploads` 记录（status=pending）。
   - 异步任务（celery/fastapi background task）读取文件、预处理并调用 `OCRService.process_document()`。
   - OCR 返回文本后写入 `ocr_results`，抽取单词写入 `words`（如不存在则创建），并把词与用户关联到 `user_words`。

2. 复习流程
   - 用户请求 `/api/v1/learning/plan/{user_id}`，后端查询 `user_words` 中 `next_review_at <= now()` 的记录并返回分页结果。
   - 用户学习并提交表现到 `/api/v1/learning/progress`，后端根据算法更新 `user_words` 并返回新的 `next_review_at`。

3. 游戏化与统计
   - 每次学习根据 `performance` 发放积分并写入 `learning_sessions.metrics`。
   - 达到条件触发 `user_achievements` 写入。


## 9. 非功能性需求

- 可用性：目标 99.9%（应用级指标）
- 性能：API 响应 < 500ms（无 OCR 场景）；OCR 为外部调用，异步处理。
- 安全：HTTPS、输入校验、认证鉴权、速率限制
- 可扩展性：后端可水平扩展，OCR 调用可并行化或接入队列
- 监控：Prometheus（指标）、Sentry（错误收集）、日志保留策略


## 10. 部署建议

- 开发：使用 `docker compose up --build` 启动 `api`, `postgres`, `redis`, `nginx`。
- 生产：使用 Kubernetes，外部负载均衡 + 自动伸缩；将静态文件与上传文件放入对象存储（S3）。
- 秘密管理：不要在 Git 中存储 `.env`，使用 Vault / AWS Secrets Manager / GCP Secret Manager。


## 11. 安全与合规

- 密钥：`GEMINI_API_KEY` 必须作为机密注入到运行环境，`.gitignore` 忽略本地 `.env`。
- 隐私：存储用户数据时遵守当地法律（GDPR 等）— 提供删除账户与数据导出接口。
- 访问控制：API 使用 JWT 并对关键操作进行权限校验。


## 12. 后续演进建议

- 增加多语言支持与 OCR 后处理（纠错、拼写校正）
- 引入模型驱动的遗忘预测（训练 LSTM / Transformer）
- 增强离线能力（桌面端缓存学习包）
- 提供导出 / 导入（Anki 格式）


---

文件位置：`docs/design-spec.md`
