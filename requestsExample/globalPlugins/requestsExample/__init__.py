import addonHandler
import api
import globalPluginHandler
import globalVars
import os
import re
from scriptHandler import script
import sys
impPath = os.path.join(os.path.abspath(os.path.dirname(__file__)), "lib")
sys.path.append(impPath)
import requests
del sys.path[-1]
import textInfos
import threading
import ui
addonHandler.initTranslation()

IP = re.compile(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    scriptCategory = _("requests example")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if globalVars.appArgs.secure:
            return

    def getIpInfo(self, ip):
        response=requests.get("https://api.2ip.ua/geo.json", params={"ip":ip})
        response.raise_for_status()
        response=response.json()
        country = response["country_rus"] if 'country_rus' in response else response["country"]
        region = response["region_rus"] if 'region_rus' in response else response["region"]
        city = response["city_rus"] if 'city_rus' in response else response["city"]
        finalString = f"country: {country}. region: {region}. city: {city}"
        ui.browseableMessage("\n".join(finalString.split(". ")), "IP information")

    def getSelectedText(self):
        obj = api.getCaretObject()
        try:
            info = obj.makeTextInfo(textInfos.POSITION_SELECTION)
            if info or not info.isCollapsed:
                return info.text.strip()
        except (RuntimeError, NotImplementedError):
            return None

    @script(
        description=_("Shows information about ip address."),
        gesture="kb:NVDA+shift+i"
    )
    def script_getIpInfo(self, gesture):
        text = self.getSelectedText()
        if not text:
            ui.message(_("Select something first"))
            return
        if not IP.search(text):
            ui.message(_("IP is not valid"))
            return
        threading.Thread(target=self.getIpInfo,args=(text,)).start()
        ui.message(_("Retrieving information for IP"))
