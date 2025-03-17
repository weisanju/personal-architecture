from fabric import Connection

from fabric_src.utils.service_manager import ServiceManagerOperator, DeployConfig

if __name__ == '__main__':
    operator = ServiceManagerOperator(Connection('47.99.62.85', user='root'))

    # 获取service目录
    operator.deploy_service_with_service_dir('/Users/weisanju/gitrepos/personal-architecture/fabric_src/service/mihomo')
