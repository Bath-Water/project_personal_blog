#!/bin/bash
# ============================================================
# project_personal_blog 一键部署脚本
# 服务器: 45.192.98.89 | 域名: 20110426.xyz
# 用法: chmod +x deploy.sh && sudo bash deploy.sh
# ============================================================
set -euo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
DOMAIN="blog.20110426.xyz"
WWW_DIR="/var/www/blog"
BACKEND_DIR="$WWW_DIR/backend"
FRONTEND_DIR="$WWW_DIR/frontend"
LOG_DIR="/var/log/blog"

ok()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn(){ echo -e "${YELLOW}[!]${NC} $1"; }
err() { echo -e "${RED}[✗]${NC} $1"; }

echo "=============================================="
echo "  project_personal_blog 部署脚本"
echo "  域名: $DOMAIN"
echo "=============================================="

# ─── 1. 基础依赖安装 ───────────────────────────────
echo ""
echo ">>> [1/8] 安装系统依赖..."
apt-get update -qq
apt-get install -y -qq curl wget git python3 python3-pip python3-venv \
  nginx certbot python3-certbot-nginx supervisor rsync unzip \
  > /dev/null 2>&1
ok "系统依赖安装完成"

# ─── 2. 创建目录结构 ───────────────────────────────
echo ""
echo ">>> [2/8] 创建目录结构..."
mkdir -p "$BACKEND_DIR" "$FRONTEND_DIR" "$LOG_DIR"
mkdir -p "$BACKEND_DIR/uploads/images" "$BACKEND_DIR/uploads/videos"
ok "目录创建完成: $WWW_DIR"

# ─── 3. 拉取代码 ───────────────────────────────────
echo ""
echo ">>> [3/8] 拉取项目代码..."
if [ -d "$WWW_DIR/.git" ]; then
  cd "$WWW_DIR" && git pull || warn "git pull 跳过（首次）"
else
  cd "$WWW_DIR"
  git clone https://github.com/Bath-Water/project_personal_blog.git ./ 2>/dev/null || {
    warn "无法从 GitHub 克隆，创建本地目录..."
    mkdir -p backend frontend
  }
fi
ok "代码同步完成"

# ─── 4. 创建 Python 虚拟环境并安装依赖 ─────────────
echo ""
echo ">>> [4/8] 创建虚拟环境 & 安装 Python 依赖..."
cd "$BACKEND_DIR"
python3 -m venv venv
source venv/bin/activate

# 如果 requirements.txt 不存在则创建
if [ ! -f requirements.txt ]; then
  cat > requirements.txt << 'PYDEPS'
fastapi>=0.100.0
uvicorn[standard]>=0.20.0
sqlalchemy[asyncio]>=2.0.0
pydantic>=2.0.0
python-jose[cryptography]>=3.3.0
bcrypt>=4.0.0
aiosqlite>=0.17.0
python-multipart>=0.0.6
pillow>=9.0.0
jieba>=0.42.0
PYDEPS
fi

pip install --upgrade pip -q
pip install -r requirements.txt -q
ok "Python 依赖安装完成"

# ─── 5. 初始化数据库 ───────────────────────────────
echo ""
echo ">>> [5/8] 初始化数据库..."
cd "$BACKEND_DIR"
python3 -c "
import logging, asyncio
logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
from app.main import app
from app.database import init_db
async def t():
    await init_db()
    print('DB tables created OK')
asyncio.run(t())
" 2>/dev/null
ok "数据库初始化完成"

# ─── 6. 配置 systemd 服务 ──────────────────────────
echo ""
echo ">>> [6/8] 配置 systemd 服务..."
cat > /etc/systemd/system/blog-backend.service << SERVICE
[Unit]
Description=Blog Backend API (FastAPI)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${BACKEND_DIR}
ExecStart=${BACKEND_DIR}/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=5
StandardOutput=append:${LOG_DIR}/backend.log
StandardError=append:${LOG_DIR}/backend-error.log

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable blog-backend
systemctl restart blog-backend
sleep 2
if systemctl is-active --quiet blog-backend; then
  ok "backend 服务已启动"
else
  err "backend 服务启动失败，查看: journalctl -u blog-backend"
fi

# ─── 7. 配置 Nginx ─────────────────────────────────
echo ""
echo ">>> [7/8] 配置 Nginx..."
# 检查是否已有同名站点
if systemctl is-active --quiet nginx; then
  nginx -s stop 2>/dev/null || true
fi

cat > /etc/nginx/sites-available/blog << NGINX
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    root $FRONTEND_DIR;
    index index.html;

    # Gzip
    gzip on;
    gzip_types text/plain text/css application/javascript application/json image/svg+xml;

    # 后端 API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # 上传文件大小限制 (50MB)
        client_max_body_size 50M;
    }

    # Swagger UI
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host \$host;
    }

    # OpenAPI JSON
    location /openapi.json {
        proxy_pass http://127.0.0.1:8000/openapi.json;
        proxy_set_header Host \$host;
    }

    # 前端静态文件
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # 缓存静态资源
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
NGINX

# 移除默认站点
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/blog /etc/nginx/sites-enabled/blog

# 测试配置
nginx -t 2>&1 | grep -q "successful" && ok "Nginx 配置正确" || err "Nginx 配置错误"
systemctl enable nginx
systemctl restart nginx
ok "Nginx 已启动"

# ─── 8. 申请 SSL 证书 (HTTPS) ──────────────────────
echo ""
echo ">>> [8/8] 申请 SSL 证书..."
# 确保 DNS 已解析（给 10 秒等待）
warn "请确认 DNS 已指向 45.192.98.89"
warn "如果 DNS 尚未生效，证书申请会失败，可稍后手动运行: certbot --nginx -d $DOMAIN"

certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email bamboo410@outlook.com \
  --redirect >> "$LOG_DIR/certbot.log" 2>&1 || warn "SSL 申请失败（DNS 可能未就绪）"

# ─── 9. 验证部署 ──────────────────────────────────
echo ""
echo ">>> 部署完成！验证中..."
sleep 2

# 后端健康检查
BACKEND_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health 2>/dev/null || echo "000")
FRONTEND_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "000")

echo ""
echo "=============================================="
echo "  🎉 部署完成！"
echo "=============================================="
echo ""
echo "  前端: http://$DOMAIN  (HTTP${FRONTEND_OK:+ [${FRONTEND_OK}]})"
echo "  后端: http://localhost:8000/api/health [${BACKEND_OK}]"
echo "  API 文档: http://$DOMAIN/docs"
echo "  SSL: https://$DOMAIN (等待 DNS 生效后自动 HTTPS)"
echo ""
echo "  常用命令:"
echo "    systemctl status blog-backend   # 查看后端状态"
echo "    journalctl -u blog-backend -f   # 查看实时日志"
echo "    systemctl status nginx           # 查看 Nginx 状态"
echo "    certbot renew                    # 续签 SSL"
echo ""
echo "  日志文件:"
echo "    ${LOG_DIR}/backend.log"
echo "    ${LOG_DIR}/backend-error.log"
echo ""

if [ "$BACKEND_OK" != "200" ]; then
  warn "后端未正常运行，请运行: journalctl -u blog-backend -n 50"
fi
if [ "$FRONTEND_OK" != "200" ]; then
  warn "前端未正常返回，请检查 Nginx 配置"
fi