#!/bin/bash
set -e

REGISTRY=registry.cn-shanghai.aliyuncs.com
NAMESPACE=yanfang
IMAGE=spider-xhs
TAG=1.0.0

FULL_IMAGE=$REGISTRY/$NAMESPACE/$IMAGE:$TAG

echo ">>> Building $IMAGE:$TAG ..."
docker build -t $IMAGE:$TAG .

echo ">>> Tagging -> $FULL_IMAGE"
docker tag $IMAGE:$TAG $FULL_IMAGE

echo ">>> Pushing $FULL_IMAGE ..."
docker push $FULL_IMAGE

echo ">>> Done: $FULL_IMAGE"

echo "按任意键退出..."
read -n 1 -s  # 等待读取一个字符，且不在屏幕上回显