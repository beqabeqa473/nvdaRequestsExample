import addonHandler
import api
import config
import globalPluginHandler
import globalVars
import gui
import os
import re
from scriptHandler import script
import sys
impPath = os.path.join(os.path.abspath(os.path.dirname(__file__)), "lib")
sys.path.append(impPath)
import pyshorteners
import requests
del sys.path[-1]
import textInfos
import threading
import ui
import wx

addonHandler.initTranslation()

IP = re.compile(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
shorteners = pyshorteners.Shortener()

confspec = {
    "service": "string(default=clckru)",
    "copyResult": "boolean(default=false)",
}
config.conf.spec["RequestsExample"] = confspec
addonConfig = config.conf["RequestsExample"]


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

    scriptCategory = _("requests example")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if globalVars.appArgs.secure:
            return
        self.shorteners = pyshorteners.Shortener()
        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(RequestsExampleSettingsPanel)

    def terminate(self):
        gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(RequestsExampleSettingsPanel)

    def getIpInfo(self, ip):
        response=requests.get("https://api.2ip.ua/geo.json", params={"ip":ip})
        response.raise_for_status()
        response=response.json()
        country = response["country_rus"] if 'country_rus' in response else response["country"]
        region = response["region_rus"] if 'region_rus' in response else response["region"]
        city = response["city_rus"] if 'city_rus' in response else response["city"]
        finalString = f"country: {country}. region: {region}. city: {city}"
        ui.browseableMessage("\n".join(finalString.split(". ")), "IP information")

    def shortenURL(self, url):
        shortener = getattr(shorteners, addonConfig["service"], None)
        shortenURL = shortener.short(url)
        if addonConfig["copyResult"]:
            if 			api.copyToClip(shortenURL):
                ui.message(_("Shortened url copied to clipboard"))
            return
        ui.browseableMessage(shortenURL, "Shortened URL")

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

    @script(
        description=_("Shortens url."),
        gesture="kb:NVDA+shift+u"
    )
    def script_shortenURL(self, gesture):
        text = self.getSelectedText()
        if not text:
            ui.message(_("Select something first"))
            return
        threading.Thread(target=self.shortenURL,args=(text,)).start()
        ui.message(_("Shortening URL"))

class RequestsExampleSettingsPanel(gui.settingsDialogs.SettingsPanel):
    title = _("Requests example")

    def makeSettings(self, sizer):
        helper = gui.guiHelper.BoxSizerHelper(self, sizer=sizer)
        self.shortenersCB = helper.addLabeledControl(_("URL shortening service:"), wx.Choice, choices=[i for i in shorteners.available_shorteners])
        self.shortenersCB.SetSelection(self.shortenersCB.FindString(addonConfig["service"]))
        self.copyResultCHK = helper.addItem(wx.CheckBox(self, label=_("Copy shortened url to clipboard")))
        self.copyResultCHK.SetValue(addonConfig["copyResult"])

    def onSave(self):
        addonConfig["service"] = self.shortenersCB.GetStringSelection()
        addonConfig["copyResult"] = self.copyResultCHK.GetValue()
