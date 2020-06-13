# -*- coding: utf-8 -*-
import wx
import wx.lib.scrolledpanel
from Client import MainClient
from Wx_Design_Objects import *
from Call_Dialogs_GUI import *
from Login_GUI import *
from Chats_GUI import *
import os
import StringIO
from io import BytesIO
from PIL import Image
import base64
from pygame import mixer

os.system('cls' if os.name=='nt' else 'clear')  # clear screen after imports
mixer.init()  # initialize audio mixer of pygame to enable sound playing


class VoiceChatApp(wx.App):
    """
    The main App class which starts the program's UI
    """
    def OnInit(self):
        """
        :returns: True

        Constructor of the main App class
        """
        self.login_frame = LoginFrame(None, title="Voice Chat")
        self.SetTopWindow(self.login_frame)
        self.login_frame.Show()
        self.program_frame = None
        self.client = MainClient()
        self.call_dialog = None
        self.being_called_sound_path = os.path.join("sounds", "rington.mp3")
        return True

    def pop_up_message(self, message):
        wx.MessageBox(message=message, style=wx.OK | wx.CENTRE)

    def inform_about_successful_register(self):
        wx.MessageBox(message="Registered Successfully", style=wx.OK | wx.CENTRE)

    def switch_to_main_program_frame(self):
        self.login_frame.Close()
        self.program_frame = ProgramFrame(None, title="Voice Chat")
        self.SetTopWindow(self.program_frame)
        self.program_frame.Show()
        if self.client.username.lower() == "skype":  # easter eggs are fun
            self.being_called_sound_path = os.path.join("sounds", "SkypeCallingMusic.mp3")
        if self.client.username.lower() == "shawty":
            self.being_called_sound_path = os.path.join("sounds", "DefaultDance.mp3")

    # The below functions are called only after program frame is up
    def enable_voice_chat_gui(self, call_group_name):
        self.destroy_call_dialog()
        self.program_frame.secondary_panel.enable_current_voice_chat_button()
        self.program_frame.secondary_panel.change_voice_chat_button_name(call_group_name)
        self.program_frame.main_panel.current_voice_chat_panel.change_voice_chat_name(call_group_name)
        self.program_frame.secondary_panel.deselect_current_selections()
        self.program_frame.main_panel.switch_to_current_voice_chat()

    def disable_voice_chat_gui(self):
        if self.program_frame.main_panel.current_voice_chat_panel.IsShown():
            self.program_frame.main_panel.switch_to_home_page()
        self.program_frame.secondary_panel.disable_current_voice_chat_button()
        self.program_frame.secondary_panel.reset_voice_chat_button_name()
        self.program_frame.main_panel.current_voice_chat_panel.participant_viewer.remove_all_participant_panels()
        self.program_frame.main_panel.current_voice_chat_panel.close_own_camera_frame()
        self.program_frame.main_panel.current_voice_chat_panel.reset_buttons()

    def stop_current_calling_dialogs(self):
        if self.call_dialog is not None:
            if isinstance(self.call_dialog, BeingCalledDialog) or isinstance(self.call_dialog, InvitedToCallDialog):
                self.call_dialog.reject_call()
            else:  # CallingDialog
                self.call_dialog.stop_calling()

    def stop_calling(self):
        if self.call_dialog is not None and isinstance(self.call_dialog, CallingUserDialog):
            self.call_dialog.stop_calling()

    def show_being_called_dialog(self, calling_users_names):
        if self.call_dialog is not None:
            self.stop_current_calling_dialogs()
        self.call_dialog = BeingCalledDialog(self.program_frame, calling_users_names, size=CALL_DIALOG_SIZE)
        mixer.music.load(self.being_called_sound_path)
        mixer.music.play(-1)  # play infinitely

    def show_invited_to_call_dialog(self, call_name, in_call_participant):
        if self.call_dialog is not None:
            self.stop_current_calling_dialogs()
        self.call_dialog = InvitedToCallDialog(self.program_frame, call_name, in_call_participant, size=CALL_DIALOG_SIZE)
        mixer.music.load(self.being_called_sound_path)
        mixer.music.play(-1)  # play infinitely

    def cancel_being_called_dialog(self):  # because of call stop
        if isinstance(self.call_dialog, BeingCalledDialog) or isinstance(self.call_dialog, InvitedToCallDialog):
            #  wx.MessageBox(message="Call Stopped", style=wx.OK | wx.CENTRE)
            self.destroy_call_dialog()

    def show_calling_dialog(self, call_user):
        self.call_dialog = CallingUserDialog(self.program_frame, call_user, size=CALL_DIALOG_SIZE)

    def cancel_calling_dialog(self, error_message=None):  # because of reject or error
        if isinstance(self.call_dialog, CallingUserDialog):
            if error_message is not None:
                wx.MessageBox(message=error_message, style=wx.OK | wx.CENTRE)
            self.destroy_call_dialog()

    def destroy_call_dialog(self):
        if self.call_dialog is not None:
            self.client.calling_username = None
            self.call_dialog.Destroy()
            self.call_dialog = None
            mixer.music.stop()

    def set_voice_chat_participants_names(self, participant_names):
        if self.program_frame.main_panel.current_voice_chat_panel is not None:
            self.program_frame.main_panel.current_voice_chat_panel.change_participant_names_string(participant_names)


class ProgramFrame(wx.Frame):
    """
    The main program frame.
    This frame is created after the user has logged in successfully.
    Contains a secondary panel in the left side of the screen and a main panel in the right
    side of the screen.
    """
    def __init__(self, parent, id=wx.ID_ANY, title="Voice Chat", pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE, name="ProgramFrame"):
        super(ProgramFrame, self).__init__(parent, id, title, pos, size, style, name)
        self.Maximize()
        self.panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.secondary_panel = SecondaryProgramPanel(self, style=wx.SUNKEN_BORDER, size=(SECONDARY_PANEL_LENGTH, wx.DisplaySize()[1]))
        self.main_panel = MainProgramPanel(self, style=wx.DOUBLE_BORDER)#, size=(wx.DisplaySize()[0] - SECONDARY_PANEL_LENGTH, wx.DisplaySize()[1]))
        self.panel_sizer.Add(self.secondary_panel, 0, wx.EXPAND)
        self.panel_sizer.Add(self.main_panel, 1, wx.EXPAND)
        self.SetSizer(self.panel_sizer)
        self.SetMinSize((800, 600))
        self.group_name_chat_panel_dict = {}  # {group_name:GroupChatPanel}
        self.contact_name_chat_panel_dict = {}  # {contact_name:ContactChatPanel}
        self.Bind(wx.EVT_MAXIMIZE, self.onMaximize, self)

    def onMaximize(self, event):
        self.main_panel.SetSize((wx.DisplaySize()[0] - SECONDARY_PANEL_LENGTH, wx.DisplaySize()[1]))
        self.main_panel.resize_panels(None)

    def switch_to_home_page(self, event):
        self.main_panel.switch_to_home_page()
        self.secondary_panel.deselect_current_selections()

    def switch_to_current_voice_chat(self, event):
        self.main_panel.switch_to_current_voice_chat()
        self.secondary_panel.deselect_current_selections()

    def add_new_group_chat(self, active_group):
        chat_panel = GroupChatPanel(self.main_panel, active_group, style=wx.EXPAND)
        chat_panel.Hide()
        self.group_name_chat_panel_dict[active_group.call_name] = chat_panel
        self.secondary_panel.add_choice_to_active_call_groups_listbox(active_group.call_name)

    def destroy_group_chat_panel(self, active_group):
        self.secondary_panel.delete_choice_in_active_call_groups_listbox(active_group.call_name)
        if self.main_panel.current_chat_panel == self.group_name_chat_panel_dict[active_group.call_name]:
            self.main_panel.current_chat_panel = None
            self.main_panel.switch_to_home_page()
        self.group_name_chat_panel_dict[active_group.call_name].Destroy()
        del self.group_name_chat_panel_dict[active_group.call_name]

    def add_new_contact_chat(self, contact):
        contact_panel = ContactChatPanel(self.main_panel, contact, style=wx.EXPAND)
        contact_panel.Hide()
        self.contact_name_chat_panel_dict[contact.username] = contact_panel
        self.secondary_panel.add_choice_to_contact_listbox(contact.username)

    def destroy_contact_chat_panel(self, contact_name):
        self.secondary_panel.delete_choice_in_contact_listbox(contact_name)
        if self.main_panel.current_chat_panel == self.contact_name_chat_panel_dict[contact_name]:
            self.main_panel.current_chat_panel = None
            self.main_panel.switch_to_home_page()
        self.contact_name_chat_panel_dict[contact_name].Destroy()
        del self.contact_name_chat_panel_dict[contact_name]

    def update_group_chat_panel(self, active_group_name):
        self.group_name_chat_panel_dict[active_group_name].update_call_information()

    def switch_to_group_chat_panel(self, active_group_name):
        self.main_panel.switch_to_chat_panel(self.group_name_chat_panel_dict[active_group_name])
        self.secondary_panel.deselect_contacts_list_selection()

    def switch_to_contact_chat_panel(self, contact_name):
        self.main_panel.switch_to_chat_panel(self.contact_name_chat_panel_dict[contact_name])
        self.secondary_panel.deselect_groups_list_selection()

    def enable_join_call_button_for_all_chats(self):
        for chat_panel in self.group_name_chat_panel_dict.values():
            chat_panel.enable_join_call_button()

    def disable_join_call_button_for_all_chats(self):
        for chat_panel in self.group_name_chat_panel_dict.values():
            chat_panel.disable_join_call_button()


class MainProgramPanel(wx.Panel):
    """
    The main panel of the program frame.
    This panel contains several other panels, only one of which will be displayed at a time.
    This panel is responsible for changing between the different screens - the main page,
    the current voice chat, or the chat panels with the contacts and groups.
    """
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr):
        super(MainProgramPanel, self).__init__(parent, id, pos, size, style, name)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.current_voice_chat_panel = VoiceChatPanel(self, size=self.GetSize(), style=wx.EXPAND)
        self.current_voice_chat_panel.Hide()
        self.home_page_panel = HomePagePanel(self, size=self.GetSize(), style=wx.EXPAND)
        self.current_chat_panel = None  # exists only when created
        self.sizer.Add(self.home_page_panel, 1, wx.EXPAND | wx.ALL)
        self.SetSizer(self.sizer)
        self.Bind(wx.EVT_SIZE, self.resize_panels, self)

    def resize_panels(self, event):
        self.current_voice_chat_panel.SetSize(self.GetSize())
        self.home_page_panel.SetSize(self.GetSize())
        if self.current_chat_panel is not None:
            self.current_chat_panel.SetSize(self.GetSize())

    def switch_to_home_page(self):
        self.current_voice_chat_panel.Hide()
        if self.current_chat_panel is not None:
            self.current_chat_panel.Hide()
        self.home_page_panel.Show()

    def switch_to_current_voice_chat(self):
        self.home_page_panel.Hide()
        if self.current_chat_panel is not None:
            self.current_chat_panel.Hide()
        self.current_voice_chat_panel.Show()

    def switch_to_chat_panel(self, chat_panel):
        if self.current_chat_panel is not None:
            self.current_chat_panel.Hide()
        self.current_chat_panel = chat_panel
        self.current_chat_panel.SetSize(self.GetSize())
        self.home_page_panel.Hide()
        self.current_voice_chat_panel.Hide()
        self.current_chat_panel.Show()


class SecondaryProgramPanel(wx.lib.scrolledpanel.ScrolledPanel):
    """
    This is the secondary panel of the program frame.
    It is always visible on the screen and allows the user to switch between the different screens
    of the main panel.
    The panel contains buttons that switch the main panel to the home page / current voice chat and two lists
    of active chat groups and contacts.
    """
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr):
        super(SecondaryProgramPanel, self).__init__(parent, id, pos, size, style, name)
        self.SetBackgroundColour(wx.LIGHT_GREY)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.current_pending_user_dialog = None
        self.init_UI()
        self.SetSizer(self.main_sizer)
        self.SetupScrolling(scroll_x=False)

    def init_UI(self):
        self.profile_picture = wx.StaticBitmap(self, -1, wx.Bitmap(DEFAULT_PROFILE_PICTURE_PATH, wx.BITMAP_TYPE_ANY), size=PROFILE_PICTURE_SIZE)
        self.profile_picture.Bind(wx.EVT_LEFT_DOWN, self.change_profile_picture)
        self.main_sizer.Add(self.profile_picture, 0, wx.ALIGN_CENTER_HORIZONTAL)

        self.username_text = TitleStaticText(self, label=wx.GetApp().client.username, style=wx.ALIGN_CENTER)
        self.main_sizer.Add(self.username_text, 0, wx.EXPAND | wx.TOP | wx.ALIGN_CENTER_HORIZONTAL, 5)
        self.main_sizer.Add(SECONDARY_PANEL_LINE_DOWN_COORDINATES)

        self.home_page_button = wx.Button(self, label="Home Page", size=(self.GetSize()[0], wx.DisplaySize()[1] * 0.05))
        self.Bind(wx.EVT_BUTTON, self.GetParent().switch_to_home_page, self.home_page_button)
        self.main_sizer.Add(self.home_page_button, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL)

        self.voice_chat_button = wx.Button(self, label=VOICE_CHAT_BUTTON_LABEL, size=(self.GetSize()[0], wx.DisplaySize()[1] * 0.05), name=VOICE_CHAT_BUTTON_NAME)
        self.voice_chat_button.Disable()
        self.Bind(wx.EVT_BUTTON, self.GetParent().switch_to_current_voice_chat, self.voice_chat_button)
        self.main_sizer.Add(self.voice_chat_button, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL)
        self.main_sizer.Add(SECONDARY_PANEL_LINE_DOWN_COORDINATES)

        active_groups_text = FontStaticText(self, NormalFont(weight=wx.FONTWEIGHT_BOLD), label="Active Call Groups", style=wx.ALIGN_CENTER)
        self.main_sizer.Add(active_groups_text, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL)
        self.active_call_groups_list_box = wx.ListBox(self, size=(self.GetSize()[0], wx.DisplaySize()[1] * 0.2), style=wx.LB_SINGLE | wx.LB_OWNERDRAW, choices=[])
        self.Bind(wx.EVT_LISTBOX, self.switch_to_group_chat_panel, self.active_call_groups_list_box)
        self.main_sizer.Add(self.active_call_groups_list_box, 0, wx.TOP | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 10)
        self.main_sizer.Add(SECONDARY_PANEL_LINE_DOWN_COORDINATES)

        contacts_text = FontStaticText(self, NormalFont(weight=wx.FONTWEIGHT_BOLD), label="Contacts", style=wx.ALIGN_CENTER)
        self.main_sizer.Add(contacts_text, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL)
        self.contacts_list_box = wx.ListBox(self, size=(self.GetSize()[0], wx.DisplaySize()[1] * 0.2), style=wx.LB_SINGLE | wx.LB_OWNERDRAW, choices=[])
        self.Bind(wx.EVT_LISTBOX, self.switch_to_contact_chat_panel, self.contacts_list_box)
        self.main_sizer.Add(self.contacts_list_box, 0, wx.TOP | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 10)
        self.main_sizer.Add(SECONDARY_PANEL_LINE_DOWN_COORDINATES)

        pending_contacts_text = FontStaticText(self, NormalFont(weight=wx.FONTWEIGHT_BOLD), label="Pending Contacts", style=wx.ALIGN_CENTER)
        self.main_sizer.Add(pending_contacts_text, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL)
        self.pending_contacts_list_box = wx.ListBox(self, size=(self.GetSize()[0], wx.DisplaySize()[1] * 0.2 / 2), style=wx.LB_SINGLE, choices=[])
        self.Bind(wx.EVT_LISTBOX, self.show_pending_contact_dialog, self.pending_contacts_list_box)
        self.main_sizer.Add(self.pending_contacts_list_box, 0, wx.TOP | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 10)

    def deselect_current_selections(self):
        self.deselect_contacts_list_selection()
        self.deselect_groups_list_selection()

    def deselect_groups_list_selection(self):
        if self.active_call_groups_list_box.GetSelection() != wx.NOT_FOUND:
            self.active_call_groups_list_box.Deselect(self.active_call_groups_list_box.GetSelection())

    def deselect_contacts_list_selection(self):
        if self.contacts_list_box.GetSelection() != wx.NOT_FOUND:
            self.contacts_list_box.Deselect(self.contacts_list_box.GetSelection())

    def show_pending_contact_dialog(self, e=None):
        if self.pending_contacts_list_box.GetSelection() != wx.NOT_FOUND:
            if self.current_pending_user_dialog is not None:
                self.current_pending_user_dialog.destroy_dialog()
            selected_pending_contact = self.pending_contacts_list_box.GetString(self.pending_contacts_list_box.GetSelection())
            self.current_pending_user_dialog = RespondToPendingContactDialog(wx.GetApp().program_frame, selected_pending_contact)
            self.pending_contacts_list_box.Deselect(self.pending_contacts_list_box.GetSelection())

    def change_voice_chat_button_name(self, call_group_name):
        self.voice_chat_button.SetLabel(VOICE_CHAT_BUTTON_LABEL + "\n" + call_group_name)

    def reset_voice_chat_button_name(self):
        self.voice_chat_button.SetLabel(VOICE_CHAT_BUTTON_LABEL)

    def enable_current_voice_chat_button(self):
        self.voice_chat_button.Enable()

    def disable_current_voice_chat_button(self):
        self.voice_chat_button.Disable()

    def switch_to_group_chat_panel(self, e):
        select_index = self.active_call_groups_list_box.GetSelection()
        selected_group_name = self.active_call_groups_list_box.GetString(select_index)
        self.GetParent().switch_to_group_chat_panel(selected_group_name)
        self.active_call_groups_list_box.SetItemBackgroundColour(select_index, wx.WHITE)

    def switch_to_contact_chat_panel(self, e):
        select_index = self.contacts_list_box.GetSelection()
        selected_group_name = self.contacts_list_box.GetString(select_index)
        self.GetParent().switch_to_contact_chat_panel(selected_group_name)
        self.contacts_list_box.SetItemBackgroundColour(select_index, wx.WHITE)

    def add_choice_to_active_call_groups_listbox(self, call_name):
        self.active_call_groups_list_box.Append(call_name)
        index = self.active_call_groups_list_box.FindString(call_name)
        self.active_call_groups_list_box.SetItemBackgroundColour(index, wx.WHITE)

    def delete_choice_in_active_call_groups_listbox(self, call_name):
        self.active_call_groups_list_box.Delete(self.active_call_groups_list_box.FindString(call_name))

    def add_choice_to_contact_listbox(self, contact_name):
        self.contacts_list_box.Append(contact_name)
        index = self.contacts_list_box.FindString(contact_name)
        self.contacts_list_box.SetItemBackgroundColour(index, wx.WHITE)

    def delete_choice_in_contact_listbox(self, contact_name):
        index = self.contacts_list_box.FindString(contact_name)
        if index != wx.NOT_FOUND:
            self.contacts_list_box.Delete(index)

    def add_choice_to_pending_contacts_listbox(self, pending_contact_name):
        self.pending_contacts_list_box.Append(pending_contact_name)

    def delete_choice_from_pending_contact_listbox(self, pending_contact_name):
        index = self.pending_contacts_list_box.FindString(pending_contact_name)
        if index != wx.NOT_FOUND:
            self.pending_contacts_list_box.Delete(index)

    def emphasize_message(self, chat_panel, chat_name):
        if isinstance(chat_panel, GroupChatPanel):
            self.emphasize_group_message(chat_name)
        elif isinstance(chat_panel, ContactChatPanel):
            self.emphasize_contact_message(chat_name)
        self.Refresh()

    def emphasize_contact_message(self, contact_name):
        if not wx.GetApp().program_frame.contact_name_chat_panel_dict[contact_name].IsShown():
            index = self.contacts_list_box.FindString(contact_name)
            self.contacts_list_box.SetItemBackgroundColour(index, wx.GREEN)

    def emphasize_group_message(self, group_name):
        if not wx.GetApp().program_frame.group_name_chat_panel_dict[group_name].IsShown():
            index = self.active_call_groups_list_box.FindString(group_name)
            self.active_call_groups_list_box.SetItemBackgroundColour(index, wx.GREEN)

    def change_profile_picture(self, e):
        select_image_dialog = wx.FileDialog(self, "Open", "", "", "Image Files|*.png;*.jpg", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if select_image_dialog.ShowModal() != wx.ID_CANCEL:
            picture_path = select_image_dialog.GetPath()
            picture_bytes = self.get_picture_bytes(picture_path)
            self.set_profile_picture(picture_bytes)
            encoded_picture_bytes = base64.b64encode(picture_bytes)
            in_call_participants_names = None
            if wx.GetApp().client.is_in_call():
                in_call_participants_names = wx.GetApp().client.voice_chat.voice_chat_client.get_participants_names_list()
            wx.GetApp().client.communication_handler.send_change_picture_message(encoded_picture_bytes, in_call_participants_names)

    def get_picture_bytes(self, picture_path):
        image = Image.open(picture_path)
        image = image.resize(PROFILE_PICTURE_SIZE, Image.ANTIALIAS)
        picture_save = BytesIO()
        image.save(picture_save, format='png')
        picture_bytes = picture_save.getvalue()
        image.close()
        picture_save.close()
        return picture_bytes

    def set_profile_picture(self, picture_bytes):
        string_picture = StringIO.StringIO(picture_bytes)
        picture_bitmap = wx.Image(string_picture).ConvertToBitmap()
        self.profile_picture.SetBitmap(picture_bitmap)


class HomePagePanel(wx.lib.scrolledpanel.ScrolledPanel):
    """
    The panel of the home page.
    Contains a user input that allows the user to search other users and then
    add them as contacts or call them.
    """
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr):
        super(HomePagePanel, self).__init__(parent, id, pos, size, style, name)
        self.SetBackgroundColour(wx.LIGHT_GREY)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.input_username = ""
        self.init_UI()
        self.SetSizer(self.main_sizer)
        self.SetupScrolling()

    def init_UI(self):
        # Title
        title_text = TitleStaticText(self, label="Welcome To VShare", style=wx.ALIGN_CENTER)
        self.main_sizer.Add(title_text, 0, wx.TOP | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 100)
        self.main_sizer.Add(DEFAULT_LINE_DOWN_COORDINATES)  # Line Down
        # Search user input
        h_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        search_user_text = FontStaticText(self, NormalFont(), label="Search User:")
        h_sizer1.Add((100, 0))
        h_sizer1.Add(search_user_text, 0)
        h_sizer1.Add((DEFAULT_GAP, 0))
        self.search_user_input = wx.TextCtrl(self, size=SEARCH_USER_INPUT_SIZE)
        self.search_user_button = wx.Button(self, label="Search User")
        self.Bind(wx.EVT_BUTTON, self.search_user, self.search_user_button)
        h_sizer1.Add(self.search_user_input)
        h_sizer1.Add((DEFAULT_GAP, 0))
        h_sizer1.Add(self.search_user_button)
        self.main_sizer.Add(h_sizer1, 0, wx.ALL | wx.EXPAND)
        self.main_sizer.Add(DEFAULT_LINE_DOWN_COORDINATES)
        # User information title
        h_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.result_text = FontStaticText(self, NormalFont(pointSize=18), label="")
        h_sizer2.AddStretchSpacer()
        h_sizer2.Add(self.result_text)
        h_sizer2.AddStretchSpacer()
        self.main_sizer.Add(h_sizer2, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL)
        self.main_sizer.Add(DEFAULT_LINE_DOWN_COORDINATES)
        # User information and interaction
        h_sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer3.AddStretchSpacer()
        self.not_found_text = FontStaticText(self, NormalFont(pointSize=16), label="")
        self.not_found_text.SetForegroundColour(wx.RED)
        h_sizer3.Add(self.not_found_text)
        h_sizer3.AddStretchSpacer()
        self.main_sizer.Add(h_sizer3, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL)
        self.main_sizer.Add(DEFAULT_LINE_DOWN_COORDINATES)


        h_sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        v_sizer4 = wx.BoxSizer(wx.VERTICAL)
        self.user_status_text = FontStaticText(self, NormalFont(), label="")
        v_sizer4.Add(self.user_status_text, 0, wx.TOP | wx.LEFT, 30)
        h_sizer5 = wx.BoxSizer(wx.HORIZONTAL)
        self.call_user_button = wx.Button(self, label="Call User", size=USER_INTERACTION_BUTTON_SIZE)
        self.add_contact_button = wx.Button(self, label="Add Contact", size=USER_INTERACTION_BUTTON_SIZE)
        self.call_user_button.Hide()
        self.add_contact_button.Hide()
        self.Bind(wx.EVT_BUTTON, self.call_input_user, self.call_user_button)
        self.Bind(wx.EVT_BUTTON, self.add_input_user_as_contact, self.add_contact_button)
        h_sizer5.Add(self.call_user_button)
        h_sizer5.Add((DEFAULT_GAP * 3, 0))
        h_sizer5.Add(self.add_contact_button)
        v_sizer4.Add(h_sizer5, 0, wx.TOP, DEFAULT_LINE_DOWN_COORDINATES[1])
        h_sizer4.Add(v_sizer4, 0, wx.LEFT, 200)

        self.requested_user_picture = wx.StaticBitmap(self, -1, wx.Bitmap(DEFAULT_PROFILE_PICTURE_PATH, wx.BITMAP_TYPE_ANY), size=PROFILE_PICTURE_SIZE)
        self.requested_user_picture.Hide()
        h_sizer4.Add(self.requested_user_picture, 0, wx.LEFT, 150)

        self.main_sizer.Add(h_sizer4, 0, wx.LEFT | wx.EXPAND)

    def search_user(self, event):
        self.input_username = self.search_user_input.GetValue()
        if self.input_username != "":
            wx.GetApp().client.communication_handler.ask_for_user_information(self.input_username)
        else:
            self.reset_search_user()

    def reset_search_user(self):
        self.result_text.SetLabel("")
        self.user_status_text.SetLabel("")
        self.not_found_text.SetLabel("")
        self.call_user_button.Hide()
        self.add_contact_button.Hide()
        self.requested_user_picture.Hide()
        self.Layout()

    def call_input_user(self, event):
        if self.input_username != "":
            wx.GetApp().stop_current_calling_dialogs()
            wx.GetApp().show_calling_dialog(self.input_username)
            wx.GetApp().client.calling_username = self.input_username
            wx.GetApp().client.request_start_call(self.input_username)

    def add_input_user_as_contact(self, event):
        if self.input_username != "":
            wx.GetApp().client.communication_handler.request_add_contact(self.input_username)

    def display_user_information(self, username, does_exits, is_online, user_encoded_picture_bytes):
        self.result_text.SetLabel(SEARCH_USER_RESULT_STRING.format(username))
        self.call_user_button.Show()
        self.add_contact_button.Show()
        if does_exits:
            self.show_existing_user_info(is_online, user_encoded_picture_bytes)
        else:
            self.call_user_button.Disable()
            self.add_contact_button.Disable()
            self.user_status_text.SetLabel("")
            self.not_found_text.SetLabel(SEARCH_USER_DOES_NOT_EXIST_STRING)
            self.requested_user_picture.Hide()
        self.Layout()

    def show_existing_user_info(self, is_online, user_encoded_picture_bytes):
        self.not_found_text.SetLabel("")
        self.add_contact_button.Enable()
        picture_bytes = base64.b64decode(user_encoded_picture_bytes)
        self.display_requested_user_picture(picture_bytes)
        if is_online:
            self.user_status_text.SetLabel(SEARCH_USER_STATUS_TEXT.format("Online"))
            self.call_user_button.Enable()
        else:
            self.user_status_text.SetLabel(SEARCH_USER_STATUS_TEXT.format("Offline"))
            self.call_user_button.Disable()

    def display_requested_user_picture(self, picture_bytes):
        string_picture = StringIO.StringIO(picture_bytes)
        picture_bitmap = wx.Image(string_picture).ConvertToBitmap()
        self.requested_user_picture.SetBitmap(picture_bitmap)
        self.requested_user_picture.Show()


def main():
    """
    The main function that runs the GUI.
    After the GUI is closed it closes the client entirely and issues an arbitrary exit.
    :return:
    """
    app = VoiceChatApp(False)
    app.MainLoop()
    # After the main app is closed.
    app.client.close_client()
    os._exit(1)


if __name__ == '__main__':
    main()


