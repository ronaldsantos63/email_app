import os
import sys

from PyQt5 import QtGui
from PyQt5.QtCore import QUrl, QSettings, Qt, QRegExp
from PyQt5.QtGui import QDesktopServices, QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineDownloadItem, QWebEngineSettings, QWebEnginePage
from PyQt5.QtWidgets import QApplication, QFileDialog, QInputDialog, QMessageBox

__application_name__ = "E-mail App"


def is_url_valid(url) -> bool:
    pattern = "((http|https)://)(www.)?[a-zA-Z0-9@:%._\\+~#?&//=]{2,256}\\.[a-z]{2,6}\\b([" \
              "-a-zA-Z0-9@:%._\\+~#?&//=]*)"
    regex_url_valid = QRegExp(pattern, Qt.CaseInsensitive, QRegExp.RegExp2)
    return regex_url_valid.exactMatch(url)


class WebView(QWebEngineView):
    __settings = QSettings("settings.ini", QSettings.IniFormat)
    __hover_url = ""

    def __init__(self):
        super(WebView, self).__init__()

        self.p = Page()
        self.setup()

        self.__connect_events()

    def setup(self):
        self.settings().setAttribute(
            QWebEngineSettings.JavascriptCanOpenWindows, True
        )
        QWebEngineSettings.globalSettings().setAttribute(
            QWebEngineSettings.PluginsEnabled, True
        )
        self.setWindowTitle(f"{__application_name__}: Loading")
        self.setWindowIcon(QIcon("logo.ico"))
        self.setPage(self.p)
        self.settings().setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        self.settings().setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        self.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)
        url = self.__get_url_from_ini()
        if not self.__get_url_from_ini():
            self.configure_domain()
        self.load(self.__get_url_from_ini())

    def configure_domain(self):
        url, ok = QInputDialog.getText(
            self,
            __application_name__,
            "Configurar domínio"
        )
        if not ok:
            if self.show_question_dialog("Deseja realmente fechar o programa?") == QMessageBox.Yes:
                sys.exit(0)
            self.configure_domain()

        if not is_url_valid(url):
            self.show_warning_dialog("Por favor digite uma url válida!\nEx: https://www.exemplo.com")
            self.configure_domain()
            return

        if str(url).find("webmail") == -1:
            if not str(url)[-1] == "/":
                url = f"{url}/webmail"
            else:
                url = f"{url}webmail"
        self.__settings.setValue("url", url)

    def show_question_dialog(self, message: str) -> int:
        return QMessageBox.question(
            self,
            __application_name__,
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

    def show_warning_dialog(self, message: str) -> int:
        return QMessageBox.warning(self, __application_name__, message)

    def createWindow(self, _type: QWebEnginePage.WebWindowType) -> 'QWebEngineView':
        if _type in [QWebEnginePage.WebBrowserWindow, QWebEnginePage.WebBrowserTab] and \
                QUrl(self.__hover_url).host() != QUrl(self.__settings.value("url", "")).host():
            QDesktopServices.openUrl(QUrl(self.__hover_url))

    def load(self, url):
        self.setUrl(QUrl(url))

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        print(f"Event: {event}")
        super().keyPressEvent(event)

    def __connect_events(self):
        self.titleChanged.connect(self.__adjust_title)
        self.page().profile().downloadRequested.connect(self.__on_download)
        self.page().linkHovered.connect(self.__update_hover_url)

    def __update_hover_url(self, url):
        self.__hover_url = url

    def __get_url_from_ini(self) -> str:
        return self.__settings.value("url", None, str)

    def __on_download(self, download: QWebEngineDownloadItem):
        path = QFileDialog.getExistingDirectory(self, caption="Escolha onde deseja salvar")
        if path:
            download.setPath(f"{path}{os.sep}{download.suggestedFileName()}")
            download.accept()

    def __show_choose_folder_dialog(self):
        dialog = QFileDialog(self, caption="Escolha onde deseja salvar")
        dialog.getExistingDirectory(self)

    def __adjust_title(self):
        self.setWindowTitle(f"{__application_name__}: {self.title()}")


class Page(QWebEnginePage):
    __settings = QSettings("settings.ini", QSettings.IniFormat)

    def __init__(self, parent=None):
        super().__init__(parent)

    def acceptNavigationRequest(self, url: QUrl, _type: 'QWebEnginePage.NavigationType', is_main_frame: bool) -> bool:
        if _type == QWebEnginePage.NavigationTypeLinkClicked and \
                url.host() != QUrl(self.__settings.value("url")).host():
            QDesktopServices.openUrl(url)
            return False
        return super().acceptNavigationRequest(url, _type, is_main_frame)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    view = WebView()
    view.showMaximized()
    sys.exit(app.exec_())
