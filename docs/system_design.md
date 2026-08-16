# 系统设计文档: personal_blog（个人博客网站）

## 1. 系统概述

personal_blog 是一款面向个人创作者的轻量级博客网站系统，采用 **单体架构（Monolith）**，前后端分离部署。

**架构选型理由：**
- 个人博客功能范围明确、模块间耦合度高，单体架构减少不必要的复杂度
- 单体架构部署简单、调试方便、性能损耗低
- 如未来扩展需要，可通过提取独立服务渐进式拆分

**系统核心功能：** 文章发布与管理（富文本、图片、视频）、分类标签体系、评论互动、全文搜索、个性化设置，支持 PC/平板/手机多端响应式展示。

---

## 2. 架构图（文本描述）

```
┌──────────────────────────────────────────────────────────────┐
│                      [Client/Browser]                         │
│              React + TypeScript + Vite + Tailwind CSS         │
│                                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │  文章列表页   │ │  文章详情页   │ │  后台管理页   │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTPS (RESTful API + JSON)
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                      [API Layer / 网关层]                      │
│              FastAPI (Python) + Pydantic 模型校验              │
│                                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │ 认证中间件   │ │ 限流/CSRF   │ │ 全局异常处理  │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                   [Business Logic Layer]                      │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │PostService│ │UserService│ │MediaSvc  │ │SearchSvc │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                     │
│  │CmtService│ │Category  │ │Settings  │                     │
│  └──────────┘ └──────────┘ └──────────┘                     │
└────────────────────────┬─────────────────────────────────────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
┌────────────────┐ ┌──────────┐ ┌──────────────┐
│   SQLite/PGSQL  │ │ 本地文件系统│ │   Redis(可选) │
│  ORM: SQLAlchemy│ │/uploads/  │ │  会话/缓存    │
└────────────────┘ └──────────┘ └──────────────┘
         Data Layer      File Layer      Cache Layer
```

### 各层职责

| 层级 | 技术 | 职责 |
|------|------|------|
| **Client/Browser** | React + TS + Vite | 用户界面渲染、交互、API 请求、路由管理 |
| **API Layer** | FastAPI + Pydantic | 路由定义、参数校验、认证鉴权、CSRF/限流中间件、统一响应格式 |
| **Business Logic** | Python Services | 业务规则、数据组装、文件处理（压缩/截图）、搜索执行 |
| **Data Layer** | SQLite / PostgreSQL | 结构化数据持久化，通过 SQLAlchemy ORM 访问 |
| **File Layer** | 本地磁盘 | 图片、视频文件存储与访问 |
| **Cache Layer** | Redis（可选） | 会话管理、热点数据缓存、限流计数 |

---

## 3. 技术栈选型

### 3.1 前端

| 技术 | 选型 | 理由 |
|------|------|------|
| 框架 | **React 18** | 生态成熟、组件化、虚拟 DOM 性能优秀 |
| 语言 | **TypeScript** | 类型安全、IDE 智能提示、减少运行时错误 |
| 构建工具 | **Vite** | 极速冷启动、HMR、产物体积优 |
| 样式 | **Tailwind CSS** | 原子化 CSS、响应式工具类、开发效率高 |
| 路由 | **React Router v6** | React 生态标准路由方案 |
| 状态管理 | **Zustand** | 轻量、无样板代码、比 Redux 简洁 |
| 富文本编辑 | **TipTap** | 基于 ProseMirror，灵活可扩展、支持图片/视频嵌入 |
| HTTP 客户端 | **Axios** | 拦截器、请求/响应转换、取消请求 |
| 响应式工具 | **原生 Tailwind 断点** | 无需额外库，直接用 `sm:` `md:` `lg:` 前缀 |

### 3.2 后端

| 技术 | 选型 | 理由 |
|------|------|------|
| 语言 | **Python 3.11** | 简洁、生态丰富、FastAPI 原生支持异步 |
| Web 框架 | **FastAPI** | 高性能、自动 OpenAPI 文档、Pydantic 数据校验 |
| ORM | **SQLAlchemy 2.x (Async)** | 成熟 ORM、支持异步、迁移工具 Alembic |
| 认证 | **python-jose (JWT) + passlib (bcrypt)** | JWT 标准库、密码哈希安全 |
| 搜索 | **jieba（中文分词）+ SQLite FTS5** | 轻量无额外依赖、SQLite 内置全文索引 |
| 图片处理 | **Pillow** | 压缩、缩放、格式转换、EXIF 读取 |
| 视频处理 | **MoviePy** | 缩略图提取、元数据读取 |

### 3.3 数据库

| 阶段 | 选型 | 理由 |
|------|------|------|
| v1.0 / 开发 | **SQLite** | 零配置、单文件部署、适合低并发 |
| 生产 | **PostgreSQL 15+** | ACID、JSON 支持、FTS、多连接、生产级稳定 |

**ORM:** SQLAlchemy 2.x，迁移工具 Alembic。SQLite 与 PostgreSQL 通过引擎配置切换，代码层面无侵入。

### 3.4 文件上传

| 阶段 | 选型 | 理由 |
|------|------|------|
| v1.0 | **本地存储** (`/uploads/`) | 简单、零运维、适合单机部署 |
| 未来 | 可替换为对象存储 (MinIO / 阿里云 OSS / AWS S3) | 接口层抽象，存储实现可插拔 |

### 3.5 部署

| 组件 | 选型 | 职责 |
|------|------|------|
| 容器化 | **Docker + Docker Compose** | 统一环境、一键启动 |
| 反向代理 | **Nginx** | 静态资源服务、SSL 终止、路由转发 |
| HTTPS | **Let's Encrypt + Certbot** | 免费证书自动续期 |
| 进程管理 | **Uvicorn + Gunicorn** | FastAPI 生产级部署（多 Worker） |

---

## 4. 数据模型（数据库 Schema）

### 4.1 表关系总览

```
users (1) ──< posts (many)
users (1) ──< comments (many)
posts (many) >── categories (1)
posts (many) >──< post_tags >──< tags (many)
posts (1) ──< comments (many)
settings (1) ──> (全局单记录)
```

### 4.2 users — 用户表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER / SERIAL | PK, AUTO | 用户 ID |
| email | VARCHAR(128) | UNIQUE, NOT NULL | 登录邮箱 |
| username | VARCHAR(64) | UNIQUE, NOT NULL | 用户名 |
| password_hash | VARCHAR(128) | NOT NULL | bcrypt 哈希密码 |
| avatar_url | VARCHAR(512) | NULLABLE | 头像图片路径 |
| is_active | BOOLEAN | DEFAULT TRUE | 账户是否启用 |
| remember_token | VARCHAR(256) | NULLABLE | 记住我令牌 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |
| updated_at | DATETIME | DEFAULT NOW(), ON UPDATE | 更新时间 |

### 4.3 posts — 文章表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER / SERIAL | PK, AUTO | 文章 ID |
| title | VARCHAR(200) | NOT NULL | 标题 |
| slug | VARCHAR(220) | UNIQUE, NOT NULL | URL 友好的唯一标识（从标题生成） |
| content | TEXT | NOT NULL | 富文本正文（HTML） |
| excerpt | VARCHAR(500) | NULLABLE | 摘要 |
| cover_url | VARCHAR(512) | NULLABLE | 封面图路径 |
| category_id | INTEGER | FK → categories.id, NULLABLE | 所属分类 |
| status | VARCHAR(16) | DEFAULT 'draft' | 枚举: draft / published |
| is_deleted | BOOLEAN | DEFAULT FALSE | 软删除标记 |
| view_count | INTEGER | DEFAULT 0 | 浏览次数 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |
| updated_at | DATETIME | DEFAULT NOW(), ON UPDATE | 更新时间 |
| published_at | DATETIME | NULLABLE | 发布时间（仅 published 时） |

**索引:** `(status, published_at DESC)`, `(is_deleted, created_at DESC)`

### 4.4 categories — 分类表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER / SERIAL | PK, AUTO | 分类 ID |
| name | VARCHAR(64) | UNIQUE, NOT NULL | 分类名称 |
| slug | VARCHAR(64) | UNIQUE, NOT NULL | URL 标识 |
| sort_order | INTEGER | DEFAULT 0 | 排序权重 |
| post_count | INTEGER | DEFAULT 0 | 文章数量（可冗余） |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |

### 4.5 tags — 标签表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER / SERIAL | PK, AUTO | 标签 ID |
| name | VARCHAR(64) | UNIQUE, NOT NULL | 标签名称 |
| slug | VARCHAR(64) | UNIQUE, NOT NULL | URL 标识 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |

### 4.6 post_tags — 文章-标签关联表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| post_id | INTEGER | FK → posts.id, PK | 文章 ID |
| tag_id | INTEGER | FK → tags.id, PK | 标签 ID |

**索引:** `(tag_id)` — 方便按标签反查文章

### 4.7 comments — 评论表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER / SERIAL | PK, AUTO | 评论 ID |
| post_id | INTEGER | FK → posts.id, NOT NULL | 所属文章 |
| user_id | INTEGER | FK → users.id, NULLABLE | 评论者（匿名时可空） |
| nickname | VARCHAR(64) | NULLABLE | 昵称（匿名用户） |
| email | VARCHAR(128) | NULLABLE | 邮箱（用于通知） |
| content | TEXT | NOT NULL | 评论正文 |
| parent_id | INTEGER | FK → comments.id, NULLABLE | 父评论（回复） |
| is_approved | BOOLEAN | DEFAULT TRUE | 是否审核通过 |
| is_deleted | BOOLEAN | DEFAULT FALSE | 软删除标记 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |

**索引:** `(post_id, created_at DESC)`

### 4.8 settings — 博客设置表（单记录表）

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER / SERIAL | PK, DEFAULT 1 | 固定为 1 |
| blog_name | VARCHAR(100) | DEFAULT 'My Blog' | 博客名称 |
| blog_description | VARCHAR(500) | NULLABLE | 博客描述 |
| theme_color | VARCHAR(7) | DEFAULT '#3B82F6' | 主题主色（HEX） |
| nav_items | JSON | NULLABLE | 导航栏配置 `[{label, url}]` |
| social_links | JSON | NULLABLE | 社交链接 `[{platform, url}]` |
| comment_enabled | BOOLEAN | DEFAULT TRUE | 是否开启评论 |
| comment_need_approval | BOOLEAN | DEFAULT FALSE | 评论是否需要审核 |
| updated_at | DATETIME | DEFAULT NOW(), ON UPDATE | 更新时间 |

---

## 5. API 设计（RESTful）

### 5.1 认证接口

```
POST   /api/auth/register      - 用户注册（邮箱 + 密码）
POST   /api/auth/login          - 用户登录（返回 JWT + refresh token）
POST   /api/auth/refresh        - 刷新访问令牌
POST   /api/auth/logout         - 登出（服务端注销会话）
GET    /api/auth/me             - 获取当前用户信息（需认证）
PUT    /api/auth/me             - 更新当前用户信息（需认证）
```

### 5.2 文章接口

```
GET    /api/posts                  - 文章列表
                            Query: page, page_size, category_id, tag_id, status
                            返回: {items[], total, page, page_size}
GET    /api/posts/{id}             - 文章详情（含正文、分类、标签、评论数）
GET    /api/posts/slug/{slug}      - 按 slug 获取文章（SEO 友好）
POST   /api/posts                  - 创建文章（需认证）
PUT    /api/posts/{id}             - 更新文章（需认证）
PATCH  /api/posts/{id}             - 部分更新（如状态切换，需认证）
DELETE /api/posts/{id}             - 软删除文章（需认证）
POST   /api/posts/{id}/preview     - 预览文章（返回渲染后的 HTML，需认证）
POST   /api/posts/{id}/publish     - 发布文章（draft → published，需认证）
GET    /api/posts/archives         - 归档列表（按年月分组）
```

### 5.3 媒体文件接口

```
POST   /api/media/upload/image     - 上传图片（FormData，多文件支持）
POST   /api/media/upload/video     - 上传视频（FormData）
POST   /api/media/embed/url        - 解析外部视频链接（YouTube/Bilibili）
GET    /api/media/{filename}       - 获取已上传文件
DELETE /api/media/{filename}       - 删除文件（需认证）
```

### 5.4 分类接口

```
GET    /api/categories             - 分类列表（含文章计数）
POST   /api/categories             - 创建分类（需认证）
PUT    /api/categories/{id}        - 更新分类（需认证）
DELETE /api/categories/{id}        - 删除分类（需认证）
```

### 5.5 标签接口

```
GET    /api/tags                   - 标签列表
POST   /api/tags                   - 创建标签（需认证）
PUT    /api/tags/{id}              - 更新标签（需认证）
DELETE /api/tags/{id}              - 删除标签（需认证）
```

### 5.6 评论接口

```
GET    /api/posts/{id}/comments    - 文章评论列表（支持分页、按时间/点赞排序）
POST   /api/posts/{id}/comments    - 发表评论
PUT    /api/comments/{id}          - 更新评论（仅作者）
DELETE /api/comments/{id}          - 软删除评论（作者或管理员）
```

### 5.7 搜索接口

```
GET    /api/search                 - 全文搜索
                            Query: q（搜索词，必填）, page, page_size
                            返回: {items[], total, highlights[]}
```

### 5.8 设置接口

```
GET    /api/settings               - 获取博客全局设置
PUT    /api/settings               - 更新博客设置（需认证）
```

---

## 6. 模块划分

### 6.1 前端模块（React Components）

```
src/
├── components/
│   ├── layout/
│   │   ├── Header           - 顶部导航栏（博客名 + 导航项 + 登录状态）
│   │   ├── Footer           - 页脚（社交链接、版权）
│   │   ├── Sidebar          - 侧边栏（分类、标签、归档）
│   │   └── MobileNav        - 移动端汉堡菜单
│   ├── common/
│   │   ├── Button           - 通用按钮
│   │   ├── Input            - 表单输入
│   │   ├── Card             - 文章列表卡片
│   │   ├── Pagination       - 分页组件
│   │   ├── Loading          - 加载状态
│   │   ├── EmptyState       - 空状态提示
│   │   ├── ImageGallery     - 图片画廊（画廊+放大）
│   │   └── VideoPlayer      - 视频播放器（本地+外部）
│   ├── posts/
│   │   ├── PostList         - 文章列表（卡片网格/列表两种布局）
│   │   ├── PostDetail       - 文章详情页（正文+评论+相关推荐）
│   │   ├── PostEditor       - 文章编辑器（TipTap 富文本 + 图片/视频上传）
│   │   ├── PostPreview      - 文章预览面板
│   │   └── SearchResults    - 搜索结果页
│   ├── admin/
│   │   ├── Dashboard        - 管理面板概览
│   │   ├── PostManage       - 文章管理（列表+批量操作）
│   │   ├── CategoryManage   - 分类管理
│   │   ├── TagManage        - 标签管理
│   │   ├── CommentManage    - 评论管理
│   │   └── SettingsPage     - 博客设置（主题、导航、社交、评论）
│   └── auth/
│       ├── LoginPage        - 登录页
│       └── RegisterPage     - 注册页
├── pages/                       # 路由页面
│   ├── Home                   - 首页（文章列表）
│   ├── Article                - 文章详情
│   ├── Category               - 分类文章列表
│   ├── Tag                    - 标签文章列表
│   ├── Search                 - 搜索结果
│   ├── Archive                - 归档页
│   └── Admin                  - 管理后台入口
├── hooks/                       # 自定义 Hooks
├── store/                       # Zustand 状态管理
├── services/                    # API 请求模块
├── utils/                       # 工具函数（日期格式化、slug 生成等）
├── types/                       # TypeScript 类型定义
└── App.tsx
```

### 6.2 后端模块（Services）

```
app/
├── main.py                   - FastAPI 应用入口、中间件注册、路由挂载
├── config.py                 - 配置管理（环境变量 + Pydantic Settings）
├── database.py               - 数据库引擎、会话管理
├── models/                   - SQLAlchemy ORM 模型
│   ├── user.py
│   ├── post.py
│   ├── category.py
│   ├── tag.py
│   ├── comment.py
│   ├── post_tag.py
│   └── setting.py
├── schemas/                  - Pydantic 请求/响应模型
│   ├── auth.py
│   ├── post.py
│   ├── media.py
│   ├── category.py
│   ├── tag.py
│   ├── comment.py
│   └── setting.py
├── routers/                  - API 路由（按资源分组）
│   ├── auth.py
│   ├── posts.py
│   ├── media.py
│   ├── categories.py
│   ├── tags.py
│   ├── comments.py
│   ├── search.py
│   └── settings.py
├── services/                 - 业务逻辑层
│   ├── auth_service.py       - 用户认证、JWT 签发/验证、密码哈希
│   ├── post_service.py       - 文章 CRUD、发布、预览、slug 生成
│   ├── media_service.py      - 文件上传、压缩、缩略图、格式校验
│   ├── category_service.py   - 分类管理
│   ├── tag_service.py        - 标签管理
│   ├── comment_service.py    - 评论管理
│   ├── search_service.py     - 全文搜索、jieba 分词、高亮
│   └── setting_service.py    - 博客设置读写
├── middleware/                - 中间件
│   ├── auth.py               - JWT 认证中间件
│   ├── csrf.py               - CSRF 防护
│   ├── rate_limit.py         - 限流
│   └── cors.py               - CORS 跨域
├── core/                     - 核心工具
│   ├── security.py           - 密码哈希、JWT、密钥管理
│   ├── file_storage.py       - 文件存储抽象（本地/可替换）
│   ├── image_processor.py    - Pillow 图片处理
│   └── video_processor.py    - MoviePy 视频处理
└── migrations/                - Alembic 数据库迁移
```

### 6.3 模块依赖关系

```
routers → schemas → services → models → database
                → core/file_storage → 本地文件系统
                → core/image_processor → Pillow
                → core/video_processor → MoviePy
```

---

## 7. 文件上传策略

### 7.1 目录结构

```
/uploads/
├── avatars/              # 用户头像
│   └── {uuid}.{ext}
├── covers/               # 文章封面图
│   └── {uuid}.{ext}
├── articles/             # 文章正文内图片
│   └── {post_id}/
│       └── {uuid}.{ext}
├── videos/               # 视频文件
│   └── {uuid}.{ext}
└── thumbnails/           # 视频缩略图
    └── {video_uuid}.{ext}
```

### 7.2 文件命名规则

- **格式：** `{UUID4}.{原始扩展名}`
- **UUID4** 保证全局唯一，避免文件名冲突和路径遍历攻击
- 目录按类型隔离，便于管理和清理

### 7.3 图片处理

| 操作 | 实现 | 说明 |
|------|------|------|
| 上传校验 | 魔数校验 + MIME 类型 | 不允许仅靠扩展名判断文件类型 |
| 尺寸限制 | 最大 4096×4096 px | 超过则等比缩放 |
| 格式转换 | 自动转为 WebP（优先） | 浏览器兼容性好，体积小 30-50% |
| 质量压缩 | WebP quality=85, JPEG quality=80 | 平衡画质与体积 |
| 懒加载 | HTML `loading="lazy"` + IntersectionObserver | 首屏性能优化 |
| 响应式 | 生成原图 + 缩略图（800px 宽） | 前端按需加载 |

### 7.4 视频处理

| 操作 | 实现 | 说明 |
|------|------|------|
| 格式限制 | MP4 (H.264) / WebM (VP9) | HTML5 原生支持 |
| 大小限制 | 单文件 ≤ 500MB | 配置项可调 |
| 缩略图 | MoviePy 提取第 1 秒帧 | 保存为 JPEG 到 thumbnails/ |
| 外部嵌入 | 解析 YouTube/Bilibili URL | 提取视频 ID，嵌入 iframe |
| 播放器 | HTML5 `<video>` 原生标签 | 无需第三方播放器库 |

---

## 8. 安全设计

### 8.1 认证流程

```
客户端                    服务器
  │                         │
  │── POST /login ─────────>│  验证邮箱密码
  │<── {access_token,       │  bcrypt 比对
  │    refresh_token} ───── │
  │                         │
  │── 后续请求带             │
  │   Authorization:        │
  │   Bearer <access>       │── 解析 JWT
  │                         │── 验签、查 expiry
  │<── 200 + data ───────── │
  │                         │
  │── POST /refresh ───────>│  验证 refresh token
  │<── 新 access_token ───── │── 签发新 token
```

- **Access Token:** 有效期 30 分钟，JWT (HS256)
- **Refresh Token:** 有效期 7 天，存入数据库（可随时吊销）
- **记住我:** 客户端存储 Refresh Token（HttpOnly Cookie），服务端验证

### 8.2 CSRF 防护

- 前后端分离架构下，API 层通过 **JWT 认证** 天然免疫 CSRF（JWT 不在 Cookie 中存储）
- 如使用 Cookie 存储 Token，额外加入 CSRF Token 验证（双重提交）
- CORS 白名单限制来源域名

### 8.3 XSS 防护

| 层面 | 措施 |
|------|------|
| 后端 | 富文本内容入库前通过 ** bleach ** 库清洗 HTML，仅允许白名单标签 |
| 前端 | React 默认转义 `{}` 输出，富文本渲染使用 ** DOMPurify ** 二次清洗 |
| HTTP 头 | `Content-Security-Policy` 限制资源加载来源 |
| Cookie | 所有 Cookie 设置 `HttpOnly` + `Secure` + `SameSite=Strict` |

### 8.4 文件上传安全

| 风险 | 防护措施 |
|------|---------|
| 恶意文件 | 魔数（Magic Number）校验文件真实类型 |
| 路径遍历 | UUID 重命名 + 固定上传目录，不信任客户端文件名 |
| 大文件攻击 | 限制单文件大小（图片 ≤ 10MB, 视频 ≤ 500MB） |
| 执行风险 | 上传目录设置 Nginx `location` 禁止 PHP/Py 等可执行 |
| MIME 检查 | 后端重新探测 MIME 类型，不只信客户端声明 |

### 8.5 密码安全

- 使用 **bcrypt**（cost factor = 12）进行密码哈希
- 注册时强制密码 ≥ 8 位，包含大小写字母 + 数字
- 密码永不明文存储或传输
- 登录接口启用限流（同一 IP 每分钟 ≤ 5 次失败）

---

## 9. 响应式设计策略

### 9.1 断点配置（Tailwind）

| 断点 | 宽度 | 设备类型 | 布局策略 |
|------|------|----------|----------|
| `sm` | ≥640px | 大手机横屏 | 单栏，缩小间距 |
| `md` | ≥768px | 平板竖屏 | 双栏（主内容 + 侧边栏） |
| `lg` | ≥1024px | 平板横屏 / 小笔记本 | 内容区加宽，卡片三列 |
| `xl` | ≥1280px | 桌面 | 最大内容宽度 1200px，居中 |
| `2xl` | ≥1536px | 大屏 | 内容区 1400px，更多留白 |

### 9.2 布局方案

```
桌面端 (≥1280px):
┌─────────────────────────────────────────────┐
│  Header (Logo + Nav + User)                 │
├──────────┬──────────────────────────────────┤
│ Sidebar  │  Main Content Area               │
│ (分类/   │  ┌─────────────────────────────┐ │
│  标签/   │  │  Post Card 1               │ │
│  归档)   │  ├─────────────────────────────┤ │
│          │  │  Post Card 2               │ │
└──────────┴──────────────────────────────────┤
│  Footer                                     │
└─────────────────────────────────────────────┘

移动端 (<768px):
┌──────────────────────┐
│  Header (汉堡菜单)    │
├──────────────────────┤
│  Main Content        │
│  ┌────────────────┐  │
│  │ Post Card 1    │  │
│  ├────────────────┤  │
│  │ Post Card 2    │  │
├──────────────────────┤
│  Collapsible Sidebar │
├──────────────────────┤
│  Footer              │
└──────────────────────┘
```

- **Flexbox:** Header/Footer 等线性布局，导航栏、按钮组
- **CSS Grid:** 文章卡片列表（桌面 3 列 → 平板 2 列 → 手机 1 列）、管理面板布局
- **Drawer / Modal:** 移动端侧边栏、文章预览弹窗

### 9.3 图片/视频响应式

| 元素 | 策略 |
|------|------|
| 文章封面 | `object-fit: cover`, 固定宽高比 (16:9)，按断点调整高度 |
| 正文图片 | `max-width: 100%`, `height: auto`, 保持原始比例 |
| 图片画廊 | CSS Grid `auto-fill, minmax(200px, 1fr)`, 移动端 2 列 |
| 视频播放器 | `aspect-ratio: 16/9`, `width: 100%`, 移动端自动缩小 |
| 缩略图 | 服务端生成 800px 宽版本，移动端优先加载小图 |

---

## 附录：项目目录结构总览

```
project_personal_blog/
├── docs/
│   └── system_design.md          ← 本文档
├── frontend/                     # React + Vite 前端
│   ├── src/
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
├── backend/                      # FastAPI 后端
│   ├── app/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic.ini
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
└── README.md
```
