import requests
import re
from PyQt5.QtCore import QRunnable

from modules.State import global_state
from modules.Working_signals import WorkerSignals

state = global_state()


class Get_Userip_Thread(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = WorkerSignals()

    def run(self):
        try:
            response = requests.get(
                url="http://189.cn/", timeout=2, proxies={"http": None, "https": None})
            state.esurfingurl = re.search(
                "http://(.+?)/", response.url).group(1)
            state.wlanacip = re.search(
                "wlanacip=(.+?)&", response.url).group(1)
            state.wlanuserip = re.search(
                "wlanuserip=(.+)", response.url).group(1)
            self.signals.print_text.emit("成功获取参数")
            self.signals.finished.emit()

        except Exception as e:
            if "'NoneType' object has no attribute 'group'" in str(e):
                self.signals.print_text.emit(f"没有从重定向的链接中获取到参数，请检查网线连接，或者是否已经能够上网了？{e}")

            else:
                self.signals.print_text.emit(f"自动获取失败，请检查以下项目\n\n①确保没有连接手机热点\n②已经登录过校园网需先断开\n③检查是否开启网络代理\n④检查网线连接\n{e}")
            
            self.signals.enable_buttoms.emit(2)
