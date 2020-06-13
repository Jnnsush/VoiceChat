
import wx
from Wx_Design_Objects import *


class InvitedToCallDialog(wx.Dialog):
    """
    A screen that pops up when the user is being called to a voice chat that he is already
    a member of it's call group.
    Contains the option to accept the call or reject the call.
    Should not exist together with the BeingCalledDialog and CallingUserDialog screens.
    """
    def __init__(self, parent, call_name, calling_users_names, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE):
        super(InvitedToCallDialog, self).__init__(parent, id, "Calling user...", pos, size, style)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.call_name = call_name
        self.calling_users_names = calling_users_names  # [str, str, str...]
        self.init_UI()
        self.SetSizer(self.main_sizer)
        self.Center()
        self.Show()

    def init_UI(self):
        h_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer1.AddStretchSpacer()
        call_name_string = FontStaticText(self, font=NormalFont(), label=INVITED_TO_JOIN_CALL_TEXT.format(self.call_name), style=wx.ALIGN_CENTER)
        h_sizer1.Add(call_name_string)
        h_sizer1.AddStretchSpacer()
        self.main_sizer.Add(h_sizer1, 0, wx.TOP | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 20)

        h_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer2.AddStretchSpacer()
        calling_users_string = ("".join(name + ", " for name in self.calling_users_names))[0:-2]  # delete last ", "
        calling_users_text = FontStaticText(self, font=NormalFont(), label=BEING_CALLED_BY_USERS_TEXT.format(calling_users_string), style=wx.ALIGN_CENTER)
        h_sizer2.Add(calling_users_text)
        h_sizer2.AddStretchSpacer()
        self.main_sizer.Add(h_sizer2, 0, wx.TOP | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 20)
        self.main_sizer.Add(DEFAULT_LINE_DOWN_COORDINATES)

        h_sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer3.AddStretchSpacer()
        self.accept_button = wx.Button(self, label="Join Call", size=USER_INTERACTION_BUTTON_SIZE)
        self.accept_button.SetFont(NormalFont(weight=wx.FONTWEIGHT_BOLD))
        self.Bind(wx.EVT_BUTTON, self.join_call, self.accept_button)
        self.reject_button = wx.Button(self, label="Reject", size=USER_INTERACTION_BUTTON_SIZE)
        self.reject_button.SetFont(NormalFont(weight=wx.FONTWEIGHT_BOLD))
        self.Bind(wx.EVT_BUTTON, self.reject_call, self.reject_button)
        h_sizer3.Add(self.accept_button)
        h_sizer3.Add(self.reject_button, 0, wx.LEFT, 20)
        h_sizer3.AddStretchSpacer()
        self.main_sizer.Add(h_sizer3, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL)

        self.Bind(wx.EVT_CLOSE, self.reject_call, self)

    def join_call(self, event=None):
        wx.GetApp().client.join_group_voice_chat(self.call_name)
        self.destroy_dialog()

    def reject_call(self, event=None):
        wx.GetApp().client.communication_handler.reject_current_call()
        self.destroy_dialog()

    def destroy_dialog(self):
        wx.GetApp().destroy_call_dialog()


class CallingUserDialog(wx.Dialog):
    """
    A screen that pops up when the user starts calling another user.
    It contains a button that allows the user to cancel the calling.
    Should not exist together with the BeingCalledDialog and InvitedToCallDialog screens.
    """
    def __init__(self, parent, call_user, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE):
        super(CallingUserDialog, self).__init__(parent, id, "Calling user...", pos, size, style)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.call_user = call_user
        self.init_UI()
        self.SetSizer(self.main_sizer)
        self.Center()
        self.Show()

    def init_UI(self):
        h_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer1.AddStretchSpacer()
        calling_user_text = FontStaticText(self, font=NormalFont(), label=CALLING_USER_TEXT.format(self.call_user), style=wx.ALIGN_CENTER)
        h_sizer1.Add(calling_user_text)
        h_sizer1.AddStretchSpacer()
        self.main_sizer.Add(h_sizer1, 0, wx.TOP | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 30)
        self.main_sizer.Add(DEFAULT_LINE_DOWN_COORDINATES)

        h_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer2.AddStretchSpacer()
        self.hang_up_button = wx.Button(self, label="Hang Up", size=USER_INTERACTION_BUTTON_SIZE)
        self.hang_up_button.SetBackgroundColour(wx.RED)
        self.hang_up_button.SetFont(NormalFont(weight=wx.FONTWEIGHT_BOLD))
        self.Bind(wx.EVT_BUTTON, self.stop_calling, self.hang_up_button)
        h_sizer2.Add(self.hang_up_button)
        h_sizer2.AddStretchSpacer()
        self.main_sizer.Add(h_sizer2, 0, wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_HORIZONTAL)

        self.Bind(wx.EVT_CLOSE, self.stop_calling, self)  # on close stop calling

    def stop_calling(self, event=None):
        wx.GetApp().client.communication_handler.stop_calling_user(self.call_user)
        wx.GetApp().destroy_call_dialog()


class BeingCalledDialog(wx.Dialog):
    """
    A screen that pops up when the user is being called by another user.
    Contains the option to accept the call or reject the call.
    Should not exist together with the CallingUserDialog and InvitedToCallDialog screens.
    """
    def __init__(self, parent, calling_users_names, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE):
        super(BeingCalledDialog, self).__init__(parent, id, "*Queue Skype Music*", pos, size, style)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.calling_users_names = calling_users_names  # [str, str, str...]
        self.init_UI()
        self.SetSizer(self.main_sizer)
        self.Center()
        self.Show()

    def init_UI(self):
        h_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer1.AddStretchSpacer()
        calling_users_string = ("".join(name + ", " for name in self.calling_users_names))[0:-2]
        calling_users_text = FontStaticText(self, font=NormalFont(), label=BEING_CALLED_BY_USERS_TEXT.format(calling_users_string), style=wx.ALIGN_CENTER)
        h_sizer1.Add(calling_users_text)
        h_sizer1.AddStretchSpacer()
        self.main_sizer.Add(h_sizer1, 0, wx.TOP | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 30)
        self.main_sizer.Add(DEFAULT_LINE_DOWN_COORDINATES)

        h_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer2.AddStretchSpacer()
        self.accept_button = wx.Button(self, label="Accept", size=USER_INTERACTION_BUTTON_SIZE)
        self.accept_button.SetFont(NormalFont(weight=wx.FONTWEIGHT_BOLD))
        self.Bind(wx.EVT_BUTTON, self.accept_call, self.accept_button)
        self.reject_button = wx.Button(self, label="Reject", size=USER_INTERACTION_BUTTON_SIZE)
        self.reject_button.SetFont(NormalFont(weight=wx.FONTWEIGHT_BOLD))
        self.Bind(wx.EVT_BUTTON, self.reject_call, self.reject_button)
        h_sizer2.Add(self.accept_button)
        h_sizer2.Add(self.reject_button, 0, wx.LEFT, 20)
        h_sizer2.AddStretchSpacer()
        self.main_sizer.Add(h_sizer2, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL)

        self.Bind(wx.EVT_CLOSE, self.reject_call, self)

    def accept_call(self, event=None):
        wx.GetApp().client.communication_handler.accept_current_call()
        self.destroy_dialog()

    def reject_call(self, event=None):
        wx.GetApp().client.communication_handler.reject_current_call()
        self.destroy_dialog()

    def destroy_dialog(self):
        wx.GetApp().destroy_call_dialog()


class RespondToPendingContactDialog(wx.Dialog):
    """
    A screen that pops up when the user clicks on a pending contact's name.
    It contains three button that allow the user to decide the pending contact's fate:
    accept the contact request, reject it or choose later.
    """
    def __init__(self, parent, pending_contact_name, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_DIALOG_STYLE):
        super(RespondToPendingContactDialog, self).__init__(parent, id, "Respond to pending contact", pos, size, style)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.pending_contact_name = pending_contact_name
        self.init_UI()
        self.SetSizer(self.main_sizer)
        self.Center()
        self.Show()

    def init_UI(self):
        h_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer1.AddStretchSpacer()
        question_text = FontStaticText(self, font=NormalFont(), label="Pending Contact: " + self.pending_contact_name, style=wx.ALIGN_CENTER)
        h_sizer1.Add(question_text)
        h_sizer1.AddStretchSpacer()
        self.main_sizer.Add(h_sizer1, 0, wx.TOP | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 30)
        self.main_sizer.Add(DEFAULT_LINE_DOWN_COORDINATES)

        h_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer2.AddStretchSpacer()
        self.accept_contact_button = wx.Button(self, label="Accept Contact", size=USER_INTERACTION_BUTTON_SIZE)
        self.accept_contact_button.SetFont(NormalFont(weight=wx.FONTWEIGHT_BOLD, pointSize=8))
        self.accept_contact_button.SetBackgroundColour(wx.GREEN)
        self.Bind(wx.EVT_BUTTON, self.accept_contact, self.accept_contact_button)
        self.reject_contact_button = wx.Button(self, label="Reject Contact", size=USER_INTERACTION_BUTTON_SIZE)
        self.reject_contact_button.SetFont(NormalFont(weight=wx.FONTWEIGHT_BOLD, pointSize=8))
        self.reject_contact_button.SetBackgroundColour(wx.RED)
        self.Bind(wx.EVT_BUTTON, self.reject_contact, self.reject_contact_button)
        self.choose_later_button = wx.Button(self, label="Choose Later", size=USER_INTERACTION_BUTTON_SIZE)
        self.choose_later_button.SetFont(NormalFont(weight=wx.FONTWEIGHT_BOLD, pointSize=8))
        self.Bind(wx.EVT_BUTTON, self.destroy_dialog, self.choose_later_button)
        h_sizer2.Add(self.accept_contact_button)
        h_sizer2.Add(self.reject_contact_button, 0, wx.LEFT, 20)
        h_sizer2.Add(self.choose_later_button, 0, wx.LEFT, 20)
        h_sizer2.AddStretchSpacer()
        self.main_sizer.Add(h_sizer2, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL)

        self.Bind(wx.EVT_CLOSE, self.destroy_dialog, self)

    def accept_contact(self, e=None):
        wx.GetApp().client.communication_handler.accept_contact(self.pending_contact_name)
        self.destroy_dialog()

    def reject_contact(self, e=None):
        wx.GetApp().client.communication_handler.reject_contact(self.pending_contact_name)
        wx.GetApp().program_frame.secondary_panel.delete_choice_from_pending_contact_listbox(self.pending_contact_name)
        self.destroy_dialog()

    def destroy_dialog(self, e=None):
        wx.GetApp().program_frame.secondary_panel.current_pending_user_dialog = None
        self.Destroy()
