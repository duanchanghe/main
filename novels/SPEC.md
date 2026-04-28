# 小说转有声书系统 (Novel to Audiobook)

## 1. 项目概述

**项目名称**: Novel2Audio
**项目类型**: 全栈移动应用 (Django Backend + Flutter Frontend)
**核心功能**: 用户上传小说文本，系统自动转换为有声书并提供在线播放
**目标用户**: 喜欢听书但视力疲劳或喜欢多任务的用户

## 2. 技术栈

### 后端
- **框架**: Django 4.x + Django REST Framework
- **数据库**: SQLite (开发环境)
- **TTS引擎**: gTTS (Google Text-to-Speech) 或 edge-tts
- **文件存储**: 本地文件系统
- **任务队列**: Django Channels (用于异步处理)

### 前端
- **框架**: Flutter 3.x
- **状态管理**: Provider
- **HTTP客户端**: Dio
- **音频播放**: just_audio
- **文件选择**: file_picker

## 3. 功能列表

### 后端功能
- [ ] 用户注册/登录 (JWT认证)
- [ ] 小说上传接口 (支持.txt文件)
- [ ] 小说列表/详情接口
- [ ] 文本转语音接口 (异步处理)
- [ ] 有声书下载/流媒体接口
- [ ] 转换进度查询接口

### 前端功能
- [ ] 用户登录/注册界面
- [ ] 小说上传界面
- [ ] 小说列表界面
- [ ] 有声书播放界面
- [ ] 下载管理界面
- [ ] 本地缓存播放

## 4. UI/UX 设计方向

### 视觉风格
- Material Design 3
- 简洁现代的卡片式设计
- 护眼深色主题为主要色调

### 配色方案
- 主色: #6366F1 (Indigo)
- 次色: #8B5CF6 (Purple)
- 背景: #1F2937 (Dark Gray)
- 文字: #F9FAFB (Light Gray)
- 强调: #10B981 (Emerald)

### 布局
- 底部导航栏 (首页/我的上传/播放/个人中心)
- 卡片式小说列表
- 悬浮播放控制器

## 5. 数据模型

### User (继承Django默认用户)
- id, username, email, password

### Novel
- id, title, author, file_path, uploaded_by, created_at, status

### Audiobook
- id, novel (FK), file_path, duration, status, created_at

## 6. API设计

### 认证
- `POST /api/auth/register/` - 用户注册
- `POST /api/auth/login/` - 用户登录
- `POST /api/auth/refresh/` - 刷新Token

### 小说
- `GET /api/novels/` - 小说列表
- `POST /api/novels/` - 上传小说
- `GET /api/novels/{id}/` - 小说详情
- `DELETE /api/novels/{id}/` - 删除小说

### 有声书
- `POST /api/audiobooks/convert/{novel_id}/` - 发起转换
- `GET /api/audiobooks/{novel_id}/` - 获取有声书
- `GET /api/audiobooks/{id}/download/` - 下载音频
- `GET /api/audiobooks/{id}/stream/` - 流媒体播放

## 7. 项目结构

```
novels/
├── backend/                 # Django后端
│   ├── manage.py
│   ├── requirements.txt
│   ├── novel2audio/        # 项目配置
│   ├── api/                # API应用
│   ├── novels/             # 小说模型
│   └── audiobooks/         # 有声书模型
└── frontend/               # Flutter前端
    ├── pubspec.yaml
    └── lib/
        ├── main.dart
        ├── screens/
        ├── widgets/
        └── services/
```
