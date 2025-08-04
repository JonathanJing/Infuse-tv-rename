#!/bin/bash

# Infuse TV Rename Tool 安装脚本

echo "🎬 Infuse TV Rename Tool 安装程序"
echo "=================================="

# 检查Python版本
echo "🔍 检查Python版本..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo "✅ 找到Python3: $PYTHON_VERSION"
else
    echo "❌ 未找到Python3，请先安装Python 3.7+"
    exit 1
fi

# 检查pip
echo "🔍 检查pip..."
if command -v pip3 &> /dev/null; then
    echo "✅ 找到pip3"
else
    echo "❌ 未找到pip3，请先安装pip"
    exit 1
fi

# 安装依赖
echo "📦 安装依赖包..."
pip3 install -r requirements.txt

# 设置执行权限
echo "🔧 设置执行权限..."
chmod +x tv_rename.py
chmod +x example.py

echo ""
echo "✅ 安装完成！"
echo ""
echo "📝 使用方法："
echo "   python3 tv_rename.py --help"
echo ""
echo "🎯 运行示例："
echo "   python3 example.py"
echo ""
echo "💡 提示：在实际使用前，请确保备份重要文件" 