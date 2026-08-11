#!/bin/bash
# GoalGo WorkBuddy 版一键安装脚本
# 用法：curl -fsSL https://raw.githubusercontent.com/Backtthefuture/goalgo/main/install-workbuddy.sh | bash

set -e

SKILL_NAME="goalgo"
REPO_URL="https://github.com/Backtthefuture/goalgo.git"
TARGET_DIR="$HOME/.workbuddy/skills/$SKILL_NAME"
TEMP_DIR=$(mktemp -d)

cleanup() {
  rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

echo "==> GoalGo WorkBuddy 版安装中..."

# 检查 git
if ! command -v git &> /dev/null; then
  echo "错误：未找到 git，请先安装 git。"
  exit 1
fi

# 如果已存在，先备份再覆盖
if [ -d "$TARGET_DIR" ]; then
  BACKUP_DIR="${TARGET_DIR}.bak.$(date +%s)"
  echo "==> 发现已有安装，备份到 $BACKUP_DIR"
  mv "$TARGET_DIR" "$BACKUP_DIR"
fi

# clone 仓库到临时目录
echo "==> 拉取仓库..."
git clone --depth 1 "$REPO_URL" "$TEMP_DIR/repo" 2> /dev/null

# 复制 workbuddy/ 目录
echo "==> 安装到 $TARGET_DIR"
mkdir -p "$(dirname "$TARGET_DIR")"
cp -r "$TEMP_DIR/repo/workbuddy" "$TARGET_DIR"

# 验证
if [ -f "$TARGET_DIR/SKILL.md" ]; then
  echo ""
  echo "安装成功！"
  echo "  位置：$TARGET_DIR"
  echo ""
  echo "下一步："
  echo "  1. 重启 WorkBuddy 或新建对话"
  echo "  2. 在对话中说出需求，GoalGo 会自动触发"
  echo ""
else
  echo "错误：安装失败，SKILL.md 未找到。"
  exit 1
fi
