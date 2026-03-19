#!/bin/bash

# 阿里云OSS前端部署脚本
# 使用前请先安装并配置ossutil

echo "开始部署前端到阿里云OSS..."

# 1. 构建前端
echo "步骤1: 构建前端项目..."
cd frontend
npm install
npm run build

if [ $? -ne 0 ]; then
    echo "❌ 前端构建失败！"
    exit 1
fi

echo "✅ 前端构建成功"

# 2. 上传到OSS
echo "步骤2: 上传文件到OSS..."
cd ..

# 请将下面的Bucket名称替换为您的实际Bucket名称
OSS_BUCKET="ai-agriculture-frontend"

# 使用ossutil上传文件
echo "正在上传文件到OSS Bucket: $OSS_BUCKET..."
ossutil cp -r frontend/dist/ oss://$OSS_BUCKET/ -f

if [ $? -ne 0 ]; then
    echo "❌ 文件上传失败！"
    echo "请确保："
    echo "1. 已安装ossutil: https://help.aliyun.com/document_detail/120075.html"
    echo "2. 已配置AccessKey: ossutil config"
    echo "3. Bucket名称正确"
    exit 1
fi

echo "✅ 文件上传成功"

# 3. 完成提示
echo ""
echo "🎉 前端部署完成！"
echo ""
echo "下一步："
echo "1. 登录OSS控制台，配置静态网站托管"
echo "2. 设置默认首页为 index.html"
echo "3. 设置404页面为 index.html（重要！解决前端路由问题）"
echo "4. 配置CDN加速（可选）"
echo ""
echo "OSS控制台: https://oss.console.aliyun.com"
echo "CDN控制台: https://cdn.console.aliyun.com"
