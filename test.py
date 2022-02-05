import wx.adv
import wx
import keyring
from getpass import getpass
from sys import stdout
from shutil import which
from subprocess import check_output, STDOUT, CalledProcessError, run, PIPE

TRAY_TOOLTIP = 'Name'
TRAY_ICON_ON = 'icon_on.png'
TRAY_ICON_OFF = 'icon_off.png'

def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.Append(item)
    return item

class TaskBarIcon(wx.adv.TaskBarIcon):
    state = False
    sudo_password = None

    if keyring.get_password("bat-icon", "sudo"):
        print("Found saved password")
    else:
        new_pass = getpass("Enter password to save:")
        keyring.set_password("bat-icon", "sudo", new_pass)
    sudo_password = keyring.get_password("bat-icon", "sudo")

    simple_stat_command = ["sudo", "-S", "tlp-stat", "-b"]

    cmd = run(
        simple_stat_command, stdout=PIPE, input=sudo_password, encoding="ascii",
    )
    tlpstat = cmd.stdout
    tlpsettinglines = tlpstat.split('\n')

    for key in tlpsettinglines:
        index = key.find("conservation_mode")
        if index != -1:
            section = key.split("conservation_mode = ", 1)[1][0]
            if section == "1":
                state = True
            else:
                state = False

    def __init__(self, frame):
        self.frame = frame
        super(TaskBarIcon, self).__init__()
        self.update_icon()
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        create_menu_item(menu, 'Refresh', self.on_refresh)
        menu.AppendSeparator()
        create_menu_item(menu, 'Exit', self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.Icon(path)
        self.SetIcon(icon, TRAY_TOOLTIP)

    def on_left_down(self, event):
        self.state = not self.state
        self.update_icon()

        "sudo tlp setcharge 0 1"
        if self.state:
            new_value = "1"
        else:
            new_value = "0"

        simple_stat_command = ["sudo", "-S", "tlp", "setcharge", "0", new_value]

        cmd = run(
            simple_stat_command, stdout=PIPE, input=self.sudo_password, encoding="ascii",
        )

        print ('Tray icon was toggled.')

    def on_refresh(self, event):
        simple_stat_command = ["sudo", "-S", "tlp-stat", "-b"]

        cmd = run(
            simple_stat_command, stdout=PIPE, input=self.sudo_password, encoding="ascii",
        )
        tlpstat = cmd.stdout
        tlpsettinglines = tlpstat.split('\n')

        for key in tlpsettinglines:
            index = key.find("conservation_mode")
            if index != -1:
                section = key.split("conservation_mode = ", 1)[1][0]
                if section == "1":
                    self.state = True
                else:
                    self.state = False

        self.update_icon()

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.Close()

    def update_icon(self):
        if self.state:
            self.set_icon(TRAY_ICON_ON)
        else:
            self.set_icon(TRAY_ICON_OFF)

class App(wx.App):
    def OnInit(self):
        frame=wx.Frame(None)
        self.SetTopWindow(frame)
        TaskBarIcon(frame)
        return True

def main():
    app = App(False)
    app.MainLoop()


if __name__ == '__main__':
    main()
