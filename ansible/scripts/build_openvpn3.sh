#!/bin/bash

# 默认值
TARGET_HOSTS="aliyun"
SOURCE_TYPE="git"
VERSION="master"
LOCAL_SOURCE=""

# 显示帮助
show_help() {
  echo "用法: $0 [选项]"
  echo "选项:"
  echo "  -h, --help             显示此帮助信息"
  echo "  -t, --target <host>    目标主机 (默认: aliyun)"
  echo "  -s, --source <type>    源码类型: git 或 local (默认: git)"
  echo "  -v, --version <ver>    git 版本/分支/标签 (默认: master)"
  echo "  -l, --local <path>     本地源码存档路径 (当 source=local 时必需)"
  echo "  -d, --dco              启用 DCO 支持 (默认: 禁用)"
  echo "  -n, --no-config        不写入配置文件 (默认: 写入)"
  echo "例子:"
  echo "  $0 -s local -l ~/Downloads/openvpn3-linux-master.zip"
  echo "  $0 -v v3.7 -d"
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
  case $1 in
    -h|--help)
      show_help
      exit 0
      ;;
    -t|--target)
      TARGET_HOSTS="$2"
      shift 2
      ;;
    -s|--source)
      SOURCE_TYPE="$2"
      shift 2
      ;;
    -v|--version)
      VERSION="$2"
      shift 2
      ;;
    -l|--local)
      LOCAL_SOURCE="$2"
      shift 2
      ;;
    -d|--dco)
      ENABLE_DCO=true
      shift
      ;;
    -n|--no-config)
      WRITE_CONFIGS=false
      shift
      ;;
    *)
      echo "未知选项: $1"
      show_help
      exit 1
      ;;
  esac
done

# 验证参数
if [ "$SOURCE_TYPE" = "local" ] && [ -z "$LOCAL_SOURCE" ]; then
  echo "错误: 使用本地源码时必须指定源码路径 (-l/--local)"
  exit 1
fi

# 构建 Ansible 额外变量
EXTRA_VARS=()
EXTRA_VARS+=("input_version=$VERSION")
EXTRA_VARS+=("input_source_type=$SOURCE_TYPE")
EXTRA_VARS+=("target_hosts=$TARGET_HOSTS")

if [ ! -z "$LOCAL_SOURCE" ]; then
  EXTRA_VARS+=("input_local_source=$LOCAL_SOURCE")
fi

if [ "$ENABLE_DCO" = true ]; then
  EXTRA_VARS+=("input_enable_dco=true")
fi

if [ "$WRITE_CONFIGS" = false ]; then
  EXTRA_VARS+=("input_write_configs=false")
fi

# 构建命令行
CMD="ansible-playbook ../build_openvpn3.yml"
for var in "${EXTRA_VARS[@]}"; do
  CMD="$CMD -e \"$var\""
done

echo "执行: $CMD"
eval $CMD 