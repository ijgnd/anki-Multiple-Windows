# -*- coding: utf-8 -*-
# Copyright: Arthur Milchior arthur@milchior.fr
# encoding: utf8
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
# Feel free to contribute to this code on https://github.com/Arthur-Milchior/anki-Multiple-Windows
# Add-on number 354407385 https://ankiweb.net/shared/info/354407385
from inspect import stack

import aqt
import sip
from anki.hooks import remHook
from aqt import DialogManager, mw
from aqt.editcurrent import EditCurrent


def shouldBeMultiple(name):
    """Whether window name may have multiple copy.

    Ensure that ["multiple"] exsits in the configuration file. The default value being True.
    """
    userOption = mw.addonManager.getConfig(__name__)
    if "multiple" not in userOption:
        userOption["multiple"] = {"default": True}
        mw.addonManager.writeConfig(__name__, userOption)
    multipleOption = userOption["multiple"]
    if name in multipleOption:
        return multipleOption[name]
    elif "default" in multipleOption:
        return multipleOption["default"]
    else:
        return True


class DialogManagerMultiple(DialogManager):
    """Associating to a window name a pair (as a list...)

    The element associated to WindowName Is composed of:
    First element is the class to use to create the window WindowName.
    Second element is always None
    """
    # We inherits from aqt.DialogManager. Thus, if something is added to
    # its _dialogs, we have access to it.

    # Every method are redefined, they use the parent's method when it makes sens.

    def __init__(self, oldDialog=None):
        if oldDialog is not None:
            DialogManagerMultiple._dialogs = oldDialog._dialogs
        super().__init__()

    _openDialogs = list()

    def open(self, name, *args, **kwargs):
        """Open a new window, with name and args.

        Or reopen the window name, if it should be single in the
        config, and is already opened.
        """
        function = self.openMany if shouldBeMultiple(name) else super().open
        return function(name, *args, **kwargs)

    def openMany(self, name, *args, **kwargs):
        """Open a new window whose kind is name.

        keyword arguments:
        args -- values passed to the opener.
        name -- the name of the window to open
        """
        (creator, _) = self._dialogs[name]
        instance = creator(*args, **kwargs)
        self._openDialogs.append(instance)
        return instance

    def markClosedMultiple(self):
        caller = stack()[2].frame.f_locals['self']
        if caller in self._openDialogs:
            self._openDialogs.remove(caller)

    def markClosed(self, name):
        """Remove the window of windowName from the set of windows. """
        # If it is a window of kind single, then call super
        # Otherwise, use inspect to figure out which is the caller
        if shouldBeMultiple(name):
            self.markClosedMultiple()
        else:
            super().markClosed(name)

    def allClosed(self):
        """
        Whether all windows (except the main window) are marked as
        closed.
        """
        return self._openDialogs == [] and super().allClosed()

    def closeAll(self, onsuccess):
        """Close all windows (except the main one). Call onsuccess when it's done.

        Return True if some window needed closing.
        None otherwise

        Keyword arguments:
        onsuccess -- the function to call when the last window is closed.
        """
        def callback():
            """Call onsuccess if all window (except main) are closed."""
            if self.allClosed():
                onsuccess()
            else:
                # still waiting for others to close
                pass
        if self.allClosed():
            onsuccess()
            return

        for instance in self._openDialogs:
            # It should be useless. I prefer to keep it to avoid erros
            if not sip.isdeleted(instance):
                if getattr(instance, "silentlyClose", False):
                    instance.close()
                    callback()
                else:
                    instance.closeWithCallback(callback)

        return super().closeAll(onsuccess)


aqt.DialogManager = DialogManagerMultiple
aqt.dialogs = DialogManagerMultiple(oldDialog=aqt.dialogs)
