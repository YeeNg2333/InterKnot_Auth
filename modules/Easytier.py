from PyQt5.QtCore import QThreadPool, pyqtSignal, QRunnable

from modules.State import global_state
from modules.Working_signals import WorkerSignals

import os 

state = global_state()

class EasyTier(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()
    def check_config(self):
        easytier_config_path = os.path.join(state.config_dir, "easytier.toml")

        if os.path.exists(easytier_config_path) is False:
            toml = f'''
                instance_name = "Misaka_Network"
                ipv4 = "10.114.114.10/24"
                dhcp = false
                listeners = ["wg://0.0.0.0:{state.easytier_port}"]

                [network_identity]
                network_name = "Misaka_Network"
                network_secret = "{state.secret_key}"

                [flags]
                bind_device = {state.bind_device}
                dev_name = "Misaka_Network"
                enable_exit_node = true
                enable_ipv6 = {state.enable_ipv6}
                '''
            with open(easytier_config_path, "w") as f:
                f.write(toml)

    def run(self):
        self.check_config()
