#!/bin/bash

# 定义变量
FRONTEND_DIR="/data/zenx_soft/aiaccountweb-standard_test/webbms"
BACKUP_DIR="/data/zenx_soft/aiaccountweb-standard_test/webbms/backup"
DIST_FILE="dist.tgz"
DIST_URL="http://web.zen-x.com.cn/aiaccountweb-standard_bms/rolweb/$DIST_FILE"
DEPLOY_DIR="/data/zenx_soft/depzen"
BACKEND_IMAGE="registry.cn-shanghai.aliyuncs.com/standard-demo/airolplay:1.2"
SQL_BACKUP_FILE="hms_bms.$(date +%Y%m%d%H%M%S).sql"
SQL_DIST_FILE="hms_bms.latest.sql"
SQL_DIST_URL="http://web.zen-x.com.cn/aiaccountweb-standard_bms/rolsql/$SQL_DIST_FILE"
SQL_HOST="10.157.1.58"
SQL_USER="root"
SQL_PASSWORD="Depz_2phaivu5S"
SQL_DB="hms"

DIST_URL="http://web.zen-x.com.cn/aiaccountweb-standard_test/web/$DIST_FILE"
RAG_FRONTEND_DIR="/data/zenx_soft/aiaccountweb-standard_test/web"
RAG_BACKUP_DIR="/data/zenx_soft/aiaccountweb-standard_test/web/backup"


# 检查参数
if [ "$#" -ne 1 ]; then
    echo "用法: $0 {1|2|3|4|5}"
    exit 1
fi

UPGRADE_WEB=false
UPGRADE_BACKEND=false
UPGRADE_SQL=false
UPGRADE_RAG_WEB=false
UPGRADE_COMPOSE_OTHERS=false

case "$1" in
    1)
        UPGRADE_WEB=true
        ;;
    2)
        UPGRADE_BACKEND=true
        ;;
    3)
        UPGRADE_SQL=true
        ;;
    4)
        UPGRADE_WEB=true
        UPGRADE_BACKEND=true
        UPGRADE_SQL=true
        ;;
    5)
        UPGRADE_WEB=true
        UPGRADE_BACKEND=true
        ;;
    6)
        UPGRADE_RAG_WEB=true
        ;;
    7)
        UPGRADE_COMPOSE_OTHERS=true
        ;;
    *)
        echo "无效的参数: $1"
        echo "用法: $0 {1|2|3|4|5|6|7}"
        exit 1
        ;;
esac

# 前端升级
if [ "$UPGRADE_WEB" = true ]; then
    echo "开始前端升级..."

    # 1. 备份dist目录
    if [ -d "$FRONTEND_DIR/dist" ]; then
        echo "备份dist目录..."
        mkdir -p "$BACKUP_DIR"
        cp -r "$FRONTEND_DIR/dist" "$BACKUP_DIR/dist_$(date +%Y%m%d%H%M%S)"
    else
        echo "dist目录不存在，跳过备份。"
    fi

    # 2. 下载升级包
    echo "从外网下载升级包..."
    wget -qO "$FRONTEND_DIR/$DIST_FILE" "$DIST_URL" --no-check-certificate

    # 3. 解压并替换dist目录
    echo "解压升级包并替换dist目录..."
    tar -zxf "$FRONTEND_DIR/$DIST_FILE" -C "$FRONTEND_DIR"
    rm -f "$FRONTEND_DIR/$DIST_FILE"

    # 4. 重启前端服务
    echo "重启前端服务..."
    cd "$DEPLOY_DIR" && docker-compose restart aiaccountweb
fi

# 后端升级
if [ "$UPGRADE_BACKEND" = true ]; then
    echo "开始后端升级..."

    # 1. 获取新的镜像
    echo "拉取新的后端镜像..."
    docker pull "$BACKEND_IMAGE"

    # 2. 重启后端服务
    echo "重启后端服务..."
    cd "$DEPLOY_DIR" && docker-compose up -d
fi

# RAG 前端升级
if [ "$UPGRADE_RAG_WEB" = true ]; then
    echo "开始 RAG 前端升级..."
    if [ -d "$RAG_FRONTEND_DIR/dist" ]; then
        echo "备份 RAG dist 目录..."
        mkdir -p "$RAG_BACKUP_DIR"
        cp -r "$RAG_FRONTEND_DIR/dist" "$RAG_BACKUP_DIR/dist_$(date +%Y%m%d%H%M%S)"
    else
        echo "RAG dist 目录不存在，跳过备份。"
    fi
    echo "下载 RAG 升级包..."
    wget -qO "$RAG_FRONTEND_DIR/$DIST_FILE" "$DIST_URL" --no-check-certificate
    echo "解压并替换 RAG dist 目录..."
    tar -zxf "$RAG_FRONTEND_DIR/$DIST_FILE" -C "$RAG_FRONTEND_DIR"
    rm -f "$RAG_FRONTEND_DIR/$DIST_FILE"
    
    # 4. 重启前端服务
    echo "重启前端服务..."
    cd "$DEPLOY_DIR" && docker-compose restart aiaccountweb
    echo "RAG 前端升级完成"
fi

# 其他 docker-compose 服务升级
if [ "$UPGRADE_COMPOSE_OTHERS" = true ]; then
    echo "开始其他服务升级 (aiindex aiquery aiaccount)..."
    cd "$DEPLOY_DIR" && docker-compose pull aiindex aiquery aiaccount
    cd "$DEPLOY_DIR" && docker-compose up aiindex aiquery aiaccount -d
    echo "其他服务升级完成"
fi

# SQL 升级
if [ "$UPGRADE_SQL" = true ]; then
    echo "开始SQL升级..."

    # 1. 备份数据库
    echo "备份数据库..."
    mysqldump --opt --default-character-set=utf8 -h "$SQL_HOST" -u "$SQL_USER" -p"$SQL_PASSWORD" "$SQL_DB" > "$BACKUP_DIR/$SQL_BACKUP_FILE"

    # 2. 下载最新的SQL文件
    echo "从外网下载最新的SQL文件..."
    wget -O "$BACKUP_DIR/$SQL_DIST_FILE" "$SQL_DIST_URL" --no-check-certificate && cd "$DEPLOY_DIR" && docker-compose down airolplay  && mysql -h "$SQL_HOST" -u "$SQL_USER" -p"$SQL_PASSWORD" "$SQL_DB" < "$BACKUP_DIR/$SQL_DIST_FILE"
    cp -a "$BACKUP_DIR/$SQL_DIST_FILE" "$BACKUP_DIR/${SQL_DIST_FILE}.$(date +%Y%m%d%H%M%S)"

       cd "$DEPLOY_DIR" &&  docker-compose up airolplay -d
fi

echo "升级完成！"
