from fabric_src.utils.service_manager import DeployConfig

deploy_config = DeployConfig(
    service_name="openvpn3",
    service_dir="openvpn",
    install_script="install.sh",
    start_script="",  # openvpn3 是以服务形式运行，不需要启动脚本
    stop_script="",
    check_script=""
) 