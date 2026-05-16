#!/bin/bash

# 创建SSL目录
mkdir -p /home/qingya/模板/nick/deploy/ssl

# 生成自签名SSL证书
openssl req -x509 -newkey rsa:4096 -nodes -keyout /home/qingya/模板/nick/deploy/ssl/hydraflow.key -out /home/qingya/模板/nick/deploy/ssl/hydraflow.crt -days 365 -subj "/CN=hydraflow.local"

echo "SSL证书已生成在 deploy/ssl/ 目录"
