# 家谱管理系统 - Genealogy SaaS Platform

一个工业级的多租户家谱管理SaaS平台，基于 Django + Flutter 构建。

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                      Flutter App                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐    │
│  │   UI    │  │ Riverpod │  │   Dio   │  │ go_router   │    │
│  └────┬────┘  └────┬────┘  └────┬────┘  └──────┬──────┘    │
└───────┼────────────┼────────────┼───────────────┼───────────┘
        │            │            │               │
        └────────────┴────────────┴───────────────┘
                              │
                    HTTPS/WSS API
                              │
┌─────────────────────────────┴───────────────────────────────┐
│                      Django Backend                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐   │
│  │   DRF    │  │   JWT    │  │  Celery  │  │  Redis    │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬─────┘   │
│       │             │              │              │          │
│  ┌────┴─────────────┴──────────────┴──────────────┴────┐   │
│  │                  PostgreSQL                            │   │
│  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌─────────┐     │   │
│  │  │ Tenant │  │ Member │  │ Relation│  │ Audit   │     │   │
│  │  └────────┘  └────────┘  └────────┘  └─────────┘     │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

## 核心功能

### SaaS 多租户
- 租户隔离 (Tenant Model)
- 多订阅计划 (Free/Basic/Pro/Enterprise)
- 配额管理 (成员数、存储、用户数)
- 邀请与成员管理

### 用户认证
- JWT Token 认证
- Token 自动刷新
- 多设备登录管理
- 安全会话控制

### 家谱管理
- 成员 CRUD
- 家族关系管理
- 族谱树可视化
- 导入/导出

### 企业级特性
- Redis 缓存
- Celery 异步任务
- API 限流
- 审计日志
- Docker 容器化

## 快速开始

### 1. 后端启动 (Docker)

```bash
cd genealogy

# 开发环境
cp backend/.env.example backend/.env
docker-compose up -d

# 访问 API
open http://localhost:8000/api/docs/
```

### 2. 后端启动 (本地开发)

```bash
cd genealogy/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 运行服务器
python manage.py runserver
```

### 3. 前端启动

```bash
cd genealogy/genealogy_app

# 安装依赖
flutter pub get

# 运行
flutter run
```

## 技术栈

### 后端
| 技术 | 用途 |
|------|------|
| Django 5.2 | Web框架 |
| Django REST Framework | API框架 |
| PostgreSQL | 主数据库 |
| Redis | 缓存/消息队列 |
| Celery | 异步任务 |
| Gunicorn | WSGI服务器 |
| WhiteNoise | 静态文件 |
| Sentry | 错误追踪 |

### 前端
| 技术 | 用途 |
|------|------|
| Flutter 3.x | 跨平台框架 |
| Riverpod | 状态管理 |
| Dio | HTTP客户端 |
| go_router | 路由管理 |
| graphview | 族谱可视化 |

## API 端点

### 认证
```
POST /api/accounts/register/    # 注册
POST /api/accounts/login/        # 登录
POST /api/accounts/logout/       # 登出
POST /api/accounts/refresh/      # 刷新Token
GET  /api/accounts/me/          # 当前用户
```

### 租户
```
POST   /api/tenants/                        # 创建租户
GET    /api/tenants/                        # 租户列表
GET    /api/tenants/{slug}/                 # 租户详情
GET    /api/tenants/{slug}/usage/           # 使用统计
POST   /api/tenants/{slug}/upgrade/         # 升级计划
```

### 家谱
```
GET    /api/family/members/                 # 成员列表
POST   /api/family/members/                 # 创建成员
GET    /api/family/members/{id}/            # 成员详情
PUT    /api/family/members/{id}/            # 更新成员
DELETE /api/family/members/{id}/            # 删除成员
GET    /api/family/members/full_tree/       # 完整族谱树
GET    /api/family/members/{id}/descendants/ # 后代列表
GET    /api/family/members/{id}/ancestors/  # 祖先列表
```

### 健康检查
```
GET /health/           # 基础健康检查
GET /health/detailed/  # 详细健康检查 (数据库、缓存)
GET /ready/            # K8s 就绪探针
```

### 文档
```
GET /api/docs/    # Swagger UI
GET /api/schema/  # OpenAPI Schema
```

## 订阅计划

| 功能 | Free | Basic | Pro | Enterprise |
|------|------|-------|-----|------------|
| 成员数 | 100 | 1,000 | 10,000 | 不限 |
| 存储 | 100MB | 1GB | 5GB | 不限 |
| 用户数 | 5 | 20 | 50 | 不限 |
| 族谱分享 | ❌ | ✅ | ✅ | ✅ |
| API访问 | ❌ | ✅ | ✅ | ✅ |
| 优先支持 | ❌ | ❌ | ✅ | ✅ |

## 部署

### Docker Compose (生产环境)

```bash
# 复制环境变量
cp .env.production.example .env

# 编辑 .env 配置数据库、Redis等

# 启动所有服务
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 查看日志
docker-compose logs -f

# 迁移数据库
docker-compose exec web python manage.py migrate
```

### 环境变量

| 变量 | 描述 | 示例 |
|------|------|------|
| DEBUG | 调试模式 | False |
| DATABASE_URL | 数据库连接 | postgres://... |
| REDIS_URL | Redis连接 | redis://localhost:6379/0 |
| DJANGO_SECRET_KEY | 密钥 | (随机字符串) |
| SENTRY_DSN | Sentry DSN | https://... |

## 开发

### 项目结构

```
genealogy/
├── backend/
│   ├── genealogy/           # Django项目配置
│   │   ├── settings.py      # 设置
│   │   ├── urls.py          # URL路由
│   │   ├── celery.py        # Celery配置
│   │   └── exceptions.py    # 自定义异常
│   ├── accounts/           # 用户认证
│   ├── family/             # 家谱管理
│   ├── tenant/             # 租户管理
│   ├── audit/              # 审计日志
│   ├── requirements.txt
│   ├── Dockerfile
│   └── manage.py
│
├── genealogy_app/
│   ├── lib/
│   │   ├── main.dart
│   │   ├── router.dart
│   │   ├── api/
│   │   ├── models/
│   │   ├── providers/
│   │   └── screens/
│   └── pubspec.yaml
│
├── docker-compose.yml
├── nginx.conf
└── README.md
```

### 常用命令

```bash
# Django
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py shell

# Celery
celery -A genealogy worker -l info
celery -A genealogy beat -l info

# Flutter
flutter pub get
flutter run -d <device_id>
flutter build apk --release
```

## 许可证

MIT License
