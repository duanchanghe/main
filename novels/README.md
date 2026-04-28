# Novel2Audio - 小说转有声书系统

一个将小说文本自动转换为有声书的全栈应用，使用 Django 后端 + Flutter 前端。

## 项目结构

```
novels/
├── backend/                 # Django 后端
│   ├── manage.py
│   ├── requirements.txt
│   ├── novel2audio/        # 项目配置
│   ├── api/               # API 应用
│   ├── novels/            # 小说模型
│   ├── audiobooks/        # 有声书模型
│   └── media/             # 上传文件存储
└── frontend/               # Flutter 前端
    ├── pubspec.yaml
    └── lib/
        ├── main.dart
        ├── screens/
        ├── widgets/
        ├── services/
        └── providers/
```

## 功能特性

### 后端功能
- 用户注册/登录 (JWT 认证)
- 小说上传 (支持 .txt 文件)
- 文本转语音 (使用 edge-tts)
- 有声书流媒体播放
- 异步转换处理

### 前端功能
- 用户登录/注册
- 小说上传
- 有声书播放
- 播放速度控制
- 深色主题 UI

## 快速开始

### 环境要求

- Python 3.9+
- Flutter 3.0+
- Node.js (可选，用于开发工具)

### 后端设置

```bash
# 进入后端目录
cd novels/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行迁移
python manage.py migrate

# 启动服务器
python manage.py runserver
```

后端服务将在 http://localhost:8000 启动

### 前端设置

```bash
# 进入前端目录
cd novels/frontend

# 获取依赖
flutter pub get

# 运行应用
flutter run
```

或者使用模拟器：
```bash
flutter run -d <device_id>
```

## API 接口

### 认证接口
| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/auth/register/ | 用户注册 |
| POST | /api/auth/login/ | 用户登录 |
| POST | /api/auth/refresh/ | 刷新 Token |
| GET | /api/user/ | 获取当前用户 |

### 小说接口
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/novels/ | 获取小说列表 |
| POST | /api/novels/ | 上传小说 |
| GET | /api/novels/{id}/ | 获取小说详情 |
| DELETE | /api/novels/{id}/ | 删除小说 |
| POST | /api/novels/{id}/convert/ | 转换为有声书 |
| GET | /api/novels/{id}/progress/ | 获取转换进度 |

### 有声书接口
| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/audiobooks/{id}/stream/ | 获取流媒体地址 |

## 技术栈

### 后端
- **框架**: Django 4.2 + Django REST Framework
- **认证**: djangorestframework-simplejwt
- **TTS**: edge-tts (微软语音合成)
- **数据库**: SQLite (开发环境)

### 前端
- **框架**: Flutter 3.x
- **状态管理**: Provider
- **HTTP**: Dio
- **音频播放**: just_audio
- **文件选择**: file_picker

## 配置说明

### 后端配置

可以在 `novels/backend/novel2audio/settings.py` 中修改以下配置：

```python
# CORS 设置 (允许所有来源，生产环境请限制)
CORS_ALLOW_ALL_ORIGINS = True

# JWT Token 有效期
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# 媒体文件存储路径
MEDIA_ROOT = BASE_DIR / 'media'
```

### 前端配置

在 `lib/services/auth_service.dart` 和 `lib/services/novel_service.dart` 中修改 API 地址：

```dart
_dio.options.baseUrl = 'http://localhost:8000/api';
```

如果使用真机测试，请将 `localhost` 替换为电脑的局域网 IP 地址。

## 使用说明

1. **注册账号**: 打开应用后注册一个新账号
2. **上传小说**: 点击底部"上传"按钮，选择 .txt 文件并填写书名作者
3. **转换为有声书**: 在书库中点击"转换为有声书"按钮
4. **播放**: 转换完成后点击"播放"按钮收听有声书

## 注意事项

- 上传的文本文件必须是 UTF-8 编码的 .txt 格式
- 语音合成使用微软 Edge 浏览器的 TTS API
- 目前仅支持中文语音合成
- 首次转换可能需要等待几秒钟

## 开发说明

### 添加新功能

1. 在对应的 models.py 中添加数据模型
2. 运行 `python manage.py makemigrations` 创建迁移
3. 在 serializers.py 中添加序列化器
4. 在 views.py 中添加视图函数
5. 在 urls.py 中添加路由

### 前端添加页面

1. 在 screens/ 目录创建新的页面组件
2. 在 home_screen.dart 的底部导航中添加新页面
3. 添加对应的 Provider 管理状态

## 许可证

MIT License
