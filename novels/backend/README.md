# 精品有声书制作系统

基于 DeepSeek AI 分析 + MiniMax TTS/Music 的智能有声书制作平台。

## 核心功能

- **智能分析**: DeepSeek 提取角色、音效、BGM 切入点
- **章节生成**: 支持按章节独立生成音频
- **多角色配音**: 每个角色自动匹配音色
- **音效增强**: 自动识别并添加场景音效
- **背景音乐**: 根据情绪自动匹配合适 BGM
- **云端存储**: 支持 MinIO 对象存储

## 业务流程

```
上传图书 → AI分析 → 生成配置 → 章节生成 → 云端存储 → 播放/下载
   ↓           ↓          ↓          ↓          ↓
  pending   analyzing   completed  chapters    minio/s3
```

## API 接口

### 认证
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/register/ | 注册 |
| POST | /api/auth/login/ | 登录 |
| POST | /api/auth/refresh/ | 刷新 Token |

### 小说管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | /api/novels/ | 列表/创建 |
| GET/PUT/DELETE | /api/novels/{id}/ | 详情/更新/删除 |
| POST | /api/novels/{id}/analyze/ | AI 分析 |
| POST | /api/novels/{id}/generate_chapter/ | 生成章节 |
| POST | /api/novels/{id}/generate_all/ | 生成全部 |
| GET | /api/novels/{id}/chapters/ | 章节列表 |
| GET | /api/novels/{id}/scenes/ | 场景列表 |
| GET | /api/novels/{id}/characters/ | 角色列表 |

### 任务管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/jobs/ | 我的任务 |
| GET | /api/jobs/{id}/ | 任务状态 |
| POST | /api/jobs/{id}/cancel/ | 取消任务 |
| GET | /api/jobs/{id}/audio/ | 获取音频 URL |
| GET | /api/jobs/{id}/stream/ | 流式播放 |

### 资源
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/voices/ | 可用音色 |
| GET | /api/sfx/ | 可用音效 |
| POST | /api/upload-url/ | 获取上传 URL |

## 环境配置

```bash
# .env
DEEPSEEK_API_KEY=your_key
MINIMAX_API_KEY=your_key
MINIMAX_GROUP_ID=your_group_id

# MinIO (可选)
USE_MINIO=false
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 运行服务
python manage.py runserver
```

## 技术栈

- **后端**: Django + DRF
- **AI 分析**: DeepSeek API
- **语音合成**: MiniMax TTS
- **背景音乐**: MiniMax Music
- **对象存储**: MinIO (可选)
