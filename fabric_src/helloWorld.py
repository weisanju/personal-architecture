from fabric import Connection

from fabric_src.utils.package_manager import PackageManagerOperator

from fabric_src.utils.service_manager import ServiceManagerOperator, DeployConfig

if __name__ == '__main__':
    operator = ServiceManagerOperator(Connection('192.168.2.2', user='root'))

    operator.deploy_service(DeployConfig(
        name="aist",
        description="云盘部署",
        exec_start="/opt/alist/alist server",
        source_path='https://github.com/AlistGo/alist/releases/download/v3.43.0/alist-linux-amd64.tar.gz',
        install_path='/opt/alist/',
        merge_config_dir="/Users/weisanju/gitrepos/personal-architecture/fabric_src/alist"
    ))
