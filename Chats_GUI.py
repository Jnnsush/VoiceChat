
import wx
import wx.lib.scrolledpanel
from Wx_Design_Objects import *
import StringIO
from io import BytesIO
from PIL import Image
from datetime import datetime
import base64
# import os.path

PARTICIPANT_PANEL_NAME = "%sPanel"
CHAT_MESSAGE_TEMPLATE = "{0} {1}> {2}"
TIME_STRING = "{0}:{1}"

MAX_CHAT_PICTURE_WIDTH = 400
MAX_CHAT_PICTURE_HEIGHT = 300

DEFAULT_SCREEN_DISPLAY_SIZE = (815, 638)
DEFAULT_CAMERA_DISPLAY_SIZE = (848, 480)  # TODO - might cause problems with different cameras.

TIME_START_INDEX = 0
TIME_END_INDEX = 5

CAMERA_FRAME_TYPE = "Camera"
SCREEN_SHARE_FRAME_TYPE = "Screen"
OWN_CAMERA_FRAME_TYPE = "OwnCamera"


class GroupChatPanel(wx.lib.scrolledpanel.ScrolledPanel):
    """
    The panel of the chat of a specific chat group.
    The chat panel contains the names of the group members who participate in the chat, the name of the chat,
    the chat itself and a button that allows a member who is not connected to the voice chat to join the voice chat.
    """
    def __init__(self, parent, active_group, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr):
        super(GroupChatPanel, self).__init__(parent, id, pos, size, style, name)
        self.SetBackgroundColour(wx.LIGHT_GREY)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.active_group = active_group
        self.init_UI()
        self.SetSizer(self.main_sizer)
        self.SetupScrolling()

    def init_UI(self):
        self.title_text = TitleStaticText(self, label=self.active_group.call_name, style=wx.ALIGN_CENTER)
        self.main_sizer.Add(self.title_text, 0, wx.TOP | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 100)
        self.main_sizer.Add(DEFAULT_LINE_DOWN_COORDINATES)

        h_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.group_members_names_text = FontStaticText(self, NormalFont(), label=CHAT_MEMBERS_NAMES_TEXT.format(self.active_group.get_group_members_names_string()), style=wx.ALIGN_CENTER)
        h_sizer1.Add(self.group_members_names_text)
        self.main_sizer.Add(h_sizer1, 0, wx.TOP | wx.LEFT | wx.EXPAND, 20)

        h_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.join_call_button = wx.Button(self, label="Join Call", size=USER_INTERACTION_BUTTON_SIZE)
        self.Bind(wx.EVT_BUTTON, self.join_call, self.join_call_button)
        h_sizer2.Add(self.join_call_button, 0, wx.LEFT | wx.EXPAND, 300)
        self.main_sizer.Add(h_sizer2, 0, wx.EXPAND | wx.TOP, 20)

        h_sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.host_name_text = FontStaticText(self, NormalFont(), label=CHAT_HOST_NAME_TEXT.format(self.active_group.host_name), style=wx.ALIGN_CENTER)
        h_sizer3.Add(self.host_name_text)
        self.main_sizer.Add(h_sizer3, 0, wx.TOP | wx.LEFT | wx.EXPAND, 20)

        h_sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        self.leave_group_button = wx.Button(self, label="Leave Group", size=USER_INTERACTION_BUTTON_SIZE)
        self.leave_group_button.SetBackgroundColour(wx.RED)
        self.Bind(wx.EVT_BUTTON, self.leave_group, self.leave_group_button)
        h_sizer4.Add(self.leave_group_button)
        self.main_sizer.Add(h_sizer4, 0, wx.TOP | wx.LEFT | wx.EXPAND, 20)

        h_sizer5 = wx.BoxSizer(wx.HORIZONTAL)
        self.chat = ChatPanel(self, self.active_group, size=(wx.DisplaySize()[0] - 450, wx.DisplaySize()[1] * 0.4), style=wx.BORDER_SUNKEN)
        h_sizer5.Add(self.chat, 0, wx.LEFT, 100)
        self.main_sizer.Add(h_sizer5, 0, wx.TOP, 80)

    def update_call_information(self):
        self.title_text.SetLabel(self.active_group.call_name)
        self.group_members_names_text.SetLabel(CHAT_MEMBERS_NAMES_TEXT.format(self.active_group.get_group_members_names_string()))
        self.host_name_text.SetLabel(CHAT_HOST_NAME_TEXT.format(self.active_group.host_name))
        self.Layout()

    def join_call(self, e):
        if not wx.GetApp().client.is_in_call():
            wx.GetApp().client.join_group_voice_chat(self.active_group.call_name)

    def leave_group(self, e):
        wx.GetApp().client.leave_call_group(self.active_group.call_name)

    def enable_join_call_button(self):
        self.join_call_button.Enable()

    def disable_join_call_button(self):
        self.join_call_button.Disable()


class ContactChatPanel(wx.lib.scrolledpanel.ScrolledPanel):
    """
    The panel of the chat of a specific contact.
    Contains the contact's name and image, the chat itself, and an option to delete the contact or call him.
    """
    def __init__(self, parent, contact, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr):
        super(ContactChatPanel, self).__init__(parent, id, pos, size, style, name)
        self.SetBackgroundColour(wx.LIGHT_GREY)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.contact = contact
        self.init_UI()
        self.SetSizer(self.main_sizer)
        self.SetupScrolling()

    def init_UI(self):
        self.title_text = TitleStaticText(self, label=self.contact.username, style=wx.ALIGN_CENTER)
        self.main_sizer.Add(self.title_text, 0, wx.TOP | wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND, 100)
        self.main_sizer.Add(DEFAULT_LINE_DOWN_COORDINATES)

        h_sizer1 = wx.BoxSizer(wx.HORIZONTAL)  # SEARCH USER STATUS TEXT ONLINE / OFFLINE
        string_picture = StringIO.StringIO(self.contact.picture_bytes)
        picture_bitmap = wx.Image(string_picture).ConvertToBitmap()
        self.profile_picture = wx.StaticBitmap(self, -1, picture_bitmap, size=PROFILE_PICTURE_SIZE)
        h_sizer1.Add(self.profile_picture, 0, wx.LEFT, 100)

        v_sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.contact_status_text =  FontStaticText(self, NormalFont(), label=SEARCH_USER_STATUS_TEXT.format("Offline"))
        v_sizer1.Add(self.contact_status_text, 0, wx.TOP, 30)
        v_sizer1.Add(DEFAULT_LINE_DOWN_COORDINATES)
        h_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.call_button = wx.Button(self, label="Call Contact", size=USER_INTERACTION_BUTTON_SIZE)
        self.Bind(wx.EVT_BUTTON, self.call_contact, self.call_button)
        h_sizer2.Add(self.call_button)
        self.delete_contact_button = wx.Button(self, label="Delete Contact", size=USER_INTERACTION_BUTTON_SIZE)
        self.Bind(wx.EVT_BUTTON, self.delete_contact, self.delete_contact_button)
        h_sizer2.Add(self.delete_contact_button, 0, wx.LEFT, DEFAULT_GAP * 3)
        v_sizer1.Add(h_sizer2, 0, wx.EXPAND)

        h_sizer1.Add(v_sizer1, 0, wx.LEFT, 50)
        self.main_sizer.Add(h_sizer1, 0, wx.TOP | wx.EXPAND, 20)

        h_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.chat = ChatPanel(self, self.contact, size=(wx.DisplaySize()[0] - 450, wx.DisplaySize()[1] * 0.4), style=wx.BORDER_SUNKEN)
        self.chat.Disable()
        h_sizer2.Add(self.chat, 0, wx.LEFT, 100)
        self.main_sizer.Add(h_sizer2, 0, wx.TOP, 100)

        if self.contact.is_connected:
            self.contact_connected()
        else:
            self.contact_went_offline()

    def call_contact(self, e):
        wx.GetApp().stop_current_calling_dialogs()
        wx.GetApp().show_calling_dialog(self.contact.username)
        wx.GetApp().client.calling_username = self.contact.username
        wx.GetApp().client.request_start_call(self.contact.username)

    def delete_contact(self, e):
        wx.GetApp().client.communication_handler.request_delete_contact(self.contact.username)
        wx.GetApp().client.delete_contact(self.contact.username)

    def contact_connected(self):
        self.contact_status_text.SetLabel(SEARCH_USER_STATUS_TEXT.format("Online"))
        self.call_button.Enable()
        self.chat.Enable()

    def contact_went_offline(self):
        self.contact_status_text.SetLabel(SEARCH_USER_STATUS_TEXT.format("Offline"))
        self.call_button.Disable()
        self.chat.Disable()

    def change_contact_picture(self, picture_bytes):
        string_picture = StringIO.StringIO(picture_bytes)
        picture_bitmap = wx.Image(string_picture).ConvertToBitmap()
        self.profile_picture.SetBitmap(picture_bitmap)


class ChatPanel(wx.Panel):
    """
    Panel of the chat itself. Contains the two parts of the chat: the chat log and and the input row.
    Dragging and dropping an image to the chat panel will send the image to the chat participants.
    """
    def __init__(self, parent, host_object, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr):
        super(ChatPanel, self).__init__(parent, id, pos, size, style, name)
        self.SetBackgroundColour(wx.LIGHT_GREY)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.host_object = host_object  # chat host object - either Contact or ActiveGroupChat
        self.init_UI()
        self.SetSizer(self.main_sizer)

    def init_UI(self):
        self.chat_log = ChatLogPanel(self, size=(self.GetSize()[0], self.GetSize()[1] * 0.8), style=wx.BORDER_DOUBLE)
        self.main_sizer.Add(self.chat_log, 0, wx.EXPAND)

        h_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.send_button = wx.Button(self, label="Send", size=(self.GetSize()[0] * 0.2, self.GetSize()[1] * 0.2))
        self.Bind(wx.EVT_BUTTON, self.send_chat_message, self.send_button)
        h_sizer1.Add(self.send_button)
        self.text_input = wx.TextCtrl(self, size=(self.GetSize()[0] * 0.8, self.GetSize()[1] * 0.2), style=wx.TE_PROCESS_ENTER)
        self.text_input.Bind(wx.EVT_TEXT_ENTER, self.send_chat_message)
        self.text_input.SetFont(NormalFont())
        file_drop_target = ChatFileDropTarget(self)
        self.SetDropTarget(file_drop_target)
        h_sizer1.Add(self.text_input)
        self.main_sizer.Add(h_sizer1, 0, wx.EXPAND)
        self.Layout()
        self.Fit()

    def send_chat_message(self, e):
        message = self.text_input.GetValue()
        if message != "":
            send_time = self.get_current_time_string()
            self.display_message(wx.GetApp().client.username, send_time, message)
            wx.GetApp().client.communication_handler.send_chat_text_message(self.host_object.get_chat_name(), self.host_object.get_chat_participants_list(), send_time, message)
            self.text_input.SetValue("")

    def send_picture(self, picture_path):
        image = Image.open(picture_path)
        image = self.chat_log.resize_image(image) # resizing image before send to decrease the amount of bytes that are sent.
        picture_save = BytesIO()
        image.save(picture_save, format='png')
        picture_bytes = picture_save.getvalue()
        send_time = self.get_current_time_string()
        self.display_picture(wx.GetApp().client.username, send_time, picture_bytes)
        encoded_picture_bytes = base64.b64encode(picture_bytes)
        wx.GetApp().client.communication_handler.send_chat_picture_message(self.host_object.get_chat_name(), self.host_object.get_chat_participants_list(), send_time, encoded_picture_bytes)

    def get_current_time_string(self):
        return str(datetime.now().time())[TIME_START_INDEX:TIME_END_INDEX]

    def display_message(self, sender_username, send_time, message):
        self.chat_log.display_message(sender_username, send_time, message)

    def display_picture(self, sender_username, send_time, picture_bytes):
        self.chat_log.display_picture(sender_username, send_time, picture_bytes)


class ChatFileDropTarget(wx.FileDropTarget):
    """
    A class that allows Drag and Drop events in wxPython.
    Used in the chat in order to allow sending images via dragging and dropping them in the chat panel.
    """
    def __init__(self, window):
        wx.FileDropTarget.__init__(self)
        self.window = window

    def OnDropFiles(self, x, y, filenames):
        if len(filenames) == 1:
            file_path = filenames[0]
            lower_file_path = file_path.lower()
            if lower_file_path.endswith(".png") or lower_file_path.endswith(".jpg"):
                self.window.send_picture(file_path)


class ChatLogPanel(wx.lib.scrolledpanel.ScrolledPanel):
    """
    The chat log itself. this is a scrollable panel that expands itself whenever needed and
    allows the displaying of both text messages and images.
    """
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr):
        super(ChatLogPanel, self).__init__(parent, id, pos, size, style, name)
        self.SetBackgroundColour((166, 166, 166))
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetupScrolling()
        self.SetSizer(self.main_sizer)

    def display_message(self, sender_username, send_time, message):
        message_panel = wx.Panel(self)
        message = CHAT_MESSAGE_TEMPLATE.format(sender_username, send_time, message)
        message_text = FontStaticText(message_panel, NormalFont(), label=message)
        self.main_sizer.Add(message_panel)
        self.Layout()
        self.GetParent().Layout()

    def display_picture(self, sender_username, send_time, picture_bytes):
        picture_panel = wx.Panel(self)
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sender_text = FontStaticText(picture_panel, NormalFont(), label=CHAT_MESSAGE_TEMPLATE.format(sender_username, send_time, ""))
        h_sizer.Add(sender_text)
        picture_bytes = self.get_resized_picture_bytes(picture_bytes)
        string_picture = StringIO.StringIO(picture_bytes)
        picture_bitmap = wx.Image(string_picture).ConvertToBitmap()
        picture = wx.StaticBitmap(picture_panel, -1, picture_bitmap)
        h_sizer.Add(picture)
        picture_panel.SetSizer(h_sizer)
        self.main_sizer.Add(picture_panel)
        self.main_sizer.Add((0, 10))
        self.Layout()
        self.GetParent().Layout()

    def get_resized_picture_bytes(self, picture_bytes):
        picture_save = BytesIO(picture_bytes)
        image = Image.open(picture_save)
        image = self.resize_image(image)
        picture_save = BytesIO()
        image.save(picture_save, format='png')
        picture_bytes = picture_save.getvalue()
        image.close()
        picture_save.close()
        return picture_bytes

    def resize_image(self, image):
        width, height = image.size
        if width > MAX_CHAT_PICTURE_WIDTH:
            width = MAX_CHAT_PICTURE_WIDTH
        if height > MAX_CHAT_PICTURE_HEIGHT:
            height = MAX_CHAT_PICTURE_HEIGHT
        image = image.resize((width, height), Image.ANTIALIAS)
        return image


class VoiceChatParticipantViewerPanel(wx.lib.scrolledpanel.ScrolledPanel):
    """
    A panel that contains information about all the voice chat participants. This is a scrollable panel that expands
    itself whenever needed and thus supports an unlimited amount of voice chat participants. Each participant has
    his own block of information that is visible in the participant viewer panel.
    """
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr):
        super(VoiceChatParticipantViewerPanel, self).__init__(parent, id, pos, size, style, name)
        self.SetBackgroundColour(wx.LIGHT_GREY)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetupScrolling(scroll_y=False)
        self.init_UI()
        self.SetSizer(self.main_sizer)

    def init_UI(self):
        self.panel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.main_sizer.Add(self.panel_sizer)

    def add_participant_panel(self, participant_name, picture_bytes):
        participant_panel_name = PARTICIPANT_PANEL_NAME % participant_name
        participant_panel = ParticipantPanel(self, participant_name, picture_bytes, name=participant_panel_name, size=PARTICIPANT_PANEL_SIZE, style=wx.BORDER_DOUBLE)
        self.panel_sizer.Add(participant_panel, 0, wx.LEFT, 100)
        # self.SetupScrolling(scroll_y=False)
        self.Layout()
        self.Fit()
        self.SetupScrolling(scroll_y=False)

    def remove_participant_panel(self, participant_name):
        if self.panel_sizer.GetChildren():
            window = self.get_participant_panel_window(participant_name)
            if window is not None:
                self.panel_sizer.Hide(window)
                if window.camera_frame is not None:
                    window.camera_frame.close_frame()
                if window.screen_frame is not None:
                    window.screen_frame.close_frame()
                window.Destroy()
                # self.SetupScrolling(scroll_y=False)
                self.Layout()
                self.Fit()

    def remove_all_participant_panels(self):
        for child in self.panel_sizer.GetChildren():
            window = child.GetWindow()
            if isinstance(window, ParticipantPanel):
                if window.camera_frame is not None:
                    window.camera_frame.close_frame()
                if window.screen_frame is not None:
                    window.screen_frame.close_frame()
            self.panel_sizer.Hide(0)
            self.panel_sizer.Remove(0)
        # self.SetupScrolling(scroll_y=False)
        self.Layout()
        self.Fit()

    def get_participant_panel_window(self, participant_name):
        participant_panel_name = PARTICIPANT_PANEL_NAME % participant_name
        for child in self.panel_sizer.GetChildren():
            if child.GetWindow().GetName() == participant_panel_name:
                return child.GetWindow()
        return None

    def set_participant_picture(self, participant_name, encoded_picture_bytes):
        picture_bytes = base64.b64decode(encoded_picture_bytes)
        participant_panel = self.get_participant_panel_window(participant_name)
        if participant_panel is not None:
            participant_panel.change_participant_picture(picture_bytes)

    def emphasize_participant_panel(self, participant_name):
        participant_panel = self.get_participant_panel_window(participant_name)
        if participant_panel is not None:
            participant_panel.emphasize_panel()

    def stop_participant_panel_emphasize(self, participant_name):
        participant_panel = self.get_participant_panel_window(participant_name)
        if participant_panel is not None:
            participant_panel.stop_panel_emphasize()

    def set_participant_camera_image(self, participant_name, image_bytes):
        participant_panel = self.get_participant_panel_window(participant_name)
        if participant_panel is not None:
            participant_panel.set_camera_image(image_bytes)

    def set_participant_screen_share_image(self, participant_name, screenshot_bytes):
        participant_panel = self.get_participant_panel_window(participant_name)
        if participant_panel is not None:
            participant_panel.set_screen_share_image(screenshot_bytes)

    def enable_participant_camera(self, participant_name):
        participant_panel = self.get_participant_panel_window(participant_name)
        if participant_panel is not None:
            participant_panel.show_camera_button.Enable()

    def disable_participant_camera(self, participant_name):
        participant_panel = self.get_participant_panel_window(participant_name)
        if participant_panel is not None:
            participant_panel.show_camera_button.Disable()
            if participant_panel.camera_frame is not None:
                participant_panel.camera_frame.close_frame()

    def enable_participant_screen_share(self, participant_name):
        participant_panel = self.get_participant_panel_window(participant_name)
        if participant_panel is not None:
            participant_panel.show_screen_share_button.Enable()

    def disable_participant_screen_share(self, participant_name):
        participant_panel = self.get_participant_panel_window(participant_name)
        if participant_panel is not None:
            participant_panel.show_screen_share_button.Disable()
            if participant_panel.screen_frame is not None:
                participant_panel.screen_frame.close_frame()


class ParticipantPicturePanel(wx.Panel):
    """
    A part of the ParticipantPanel object. this is class that wraps the participant's picture in the
    ParticipantPanel object.
    """
    def __init__(self, parent, picture_bytes, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr):
        super(ParticipantPicturePanel, self).__init__(parent, id, pos, size, style, name)
        self.SetBackgroundColour(wx.LIGHT_GREY)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        string_picture = StringIO.StringIO(picture_bytes)
        picture_bitmap = wx.Image(string_picture).ConvertToBitmap()
        self.participant_picture = wx.StaticBitmap(self, -1, picture_bitmap, size=PROFILE_PICTURE_SIZE)
        self.main_sizer.Add(self.participant_picture, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND)
        self.SetSizer(self.main_sizer)


class ParticipantPanel(wx.Panel):
    """
    A panel of a specific participant in the ParticipantViewerPanel. The panel contains information and interactive
    buttons. Contains the participant's name and picture, and an option to view his screen share and camera share
    (which are enabled only if the participant is actually sending said data types).
    """
    def __init__(self, parent, participant_name, picture_bytes, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr):
        super(ParticipantPanel, self).__init__(parent, id, pos, size, style, name)
        self.SetBackgroundColour(wx.LIGHT_GREY)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.participant_name = participant_name
        self.camera_frame = None
        self.screen_frame = None
        self.init_UI(picture_bytes)
        self.SetSizer(self.main_sizer)

    def init_UI(self, picture_bytes):
        self.participant_picture_panel = ParticipantPicturePanel(self, picture_bytes)
        self.main_sizer.Add(self.participant_picture_panel, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.EXPAND)

        participant_name_text = FontStaticText(self, NormalFont(), label=self.participant_name)
        participant_name_text.SetBackgroundColour(wx.LIGHT_GREY)
        self.main_sizer.Add(participant_name_text, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP, 10)

        h_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.show_camera_button = wx.Button(self, label="Show Camera", size=(self.GetSize()[0] / 2, 40))
        self.Bind(wx.EVT_BUTTON, self.show_participant_camera, self.show_camera_button)
        self.show_camera_button.Disable()
        h_sizer2.Add(self.show_camera_button)
        self.show_screen_share_button = wx.Button(self, label="Show Screen", size=(self.GetSize()[0] / 2, 40))
        self.Bind(wx.EVT_BUTTON, self.show_participant_screen_share, self.show_screen_share_button)
        self.show_screen_share_button.Disable()
        h_sizer2.Add(self.show_screen_share_button, 0, wx.EXPAND)
        self.main_sizer.Add(h_sizer2, 0, wx.TOP, 10)

    def emphasize_panel(self):
        self.participant_picture_panel.SetBackgroundColour((132, 175, 244))
        self.participant_picture_panel.Layout()

    def stop_panel_emphasize(self):
        self.participant_picture_panel.SetBackgroundColour(wx.LIGHT_GREY)
        self.participant_picture_panel.Layout()

    def show_participant_camera(self, e):
        if self.camera_frame is None:
            self.camera_frame = PictureDisplayFrame(self, CAMERA_FRAME_TYPE, title=self.participant_name, size=DEFAULT_CAMERA_DISPLAY_SIZE)
            self.camera_frame.Show()
            self.show_camera_button.SetBackgroundColour((177, 255, 114))
        else:
            self.camera_frame.Restore()
            self.camera_frame.Raise()

    def set_camera_image(self, image_bytes):
        if self.camera_frame is not None:
            self.camera_frame.set_image(image_bytes)

    def show_participant_screen_share(self, e):
        if self.screen_frame is None:
            self.screen_frame = PictureDisplayFrame(self, SCREEN_SHARE_FRAME_TYPE, title=self.participant_name, size=DEFAULT_SCREEN_DISPLAY_SIZE)
            self.screen_frame.Show()
            self.show_screen_share_button.SetBackgroundColour((177, 255, 114))
        else:
            self.screen_frame.Restore()
            self.screen_frame.Raise()

    def set_screen_share_image(self, image_bytes):
        if self.screen_frame is not None:
            self.screen_frame.set_image(image_bytes)

    def change_participant_picture(self, picture_bytes):
        string_picture = StringIO.StringIO(picture_bytes)
        picture_bitmap = wx.Image(string_picture).ConvertToBitmap()
        self.participant_picture_panel.participant_picture.SetBitmap(picture_bitmap)
        self.participant_picture_panel.Layout()


class VoiceChatPanel(wx.lib.scrolledpanel.ScrolledPanel):
    """
    The panel of the current voice chat.
    Contains the other participants in the voice chat and their information.
    Contains all the features that the voice chat offers.
    The user can leave the voice chat via the leave button.
    """
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr):
        super(VoiceChatPanel, self).__init__(parent, id, pos, size, style, name)
        self.SetBackgroundColour(wx.LIGHT_GREY)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.participant_names_string = ""
        self.own_camera_frame = None
        self.init_UI()
        self.SetSizer(self.main_sizer)
        self.SetupScrolling()

    def init_UI(self):
        self.title_text = TitleStaticText(self, label="Current Voice Chat", style=wx.ALIGN_CENTER)
        self.main_sizer.Add(self.title_text, 0, wx.TOP | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, wx.DisplaySize()[1] * 0.1)

        h_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.participants_text = FontStaticText(self, NormalFont(), label=VOICE_CHAT_PARTICIPANT_NAMES_TEXT.format(self.participant_names_string), style=wx.ALIGN_CENTER)
        h_sizer1.Add(self.participants_text)
        self.main_sizer.Add(self.participants_text, 0, wx.TOP | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, wx.DisplaySize()[1] * 0.05)

        self.main_sizer.Add((0, wx.DisplaySize()[1] * 0.05))
        h_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.participant_viewer = VoiceChatParticipantViewerPanel(self, size=(wx.DisplaySize()[0] - 450, PARTICIPANT_PANEL_SIZE[1] + 20), style=wx.BORDER_SUNKEN)
        h_sizer2.Add(self.participant_viewer, 0, wx.EXPAND | wx.LEFT, 100)
        self.main_sizer.Add(h_sizer2)

        self.main_sizer.Add((0, wx.DisplaySize()[1] * 0.1))
        h_sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer3.AddStretchSpacer()
        self.leave_voice_chat_button = wx.Button(self, label="Leave", size=(200, 60))
        self.leave_voice_chat_button.SetBackgroundColour(wx.RED)
        self.leave_voice_chat_button.SetFont(NormalFont(weight=wx.FONTWEIGHT_BOLD))
        self.Bind(wx.EVT_BUTTON, self.leave_voice_chat, self.leave_voice_chat_button)
        h_sizer3.Add(self.leave_voice_chat_button)
        self.mute_button = wx.Button(self, label="Mute", size=(200, 60))
        self.mute_button.SetFont(NormalFont(weight=wx.FONTWEIGHT_BOLD))
        self.Bind(wx.EVT_BUTTON, self.toggle_mute, self.mute_button)
        h_sizer3.Add(self.mute_button, 0, wx.LEFT, 20)
        self.camera_button = wx.Button(self, label="Toggle Camera", size=(200, 60))
        self.camera_button.SetFont(NormalFont(weight=wx.FONTWEIGHT_BOLD))
        self.Bind(wx.EVT_BUTTON, self.toggle_camera, self.camera_button)
        h_sizer3.Add(self.camera_button, 0, wx.LEFT, 20)
        self.screen_share_button = wx.Button(self, label="Toggle Screen Share", size=(200, 60))
        self.screen_share_button.SetFont(NormalFont(weight=wx.FONTWEIGHT_BOLD))
        self.Bind(wx.EVT_BUTTON, self.toggle_screen_share, self.screen_share_button)
        h_sizer3.Add(self.screen_share_button, 0, wx.LEFT, 20)
        self.show_own_camera_button = wx.Button(self, label="Your Camera", size=(200, 60))
        self.show_own_camera_button.SetFont(NormalFont(weight=wx.FONTWEIGHT_BOLD))
        self.Bind(wx.EVT_BUTTON, self.show_own_camera, self.show_own_camera_button)
        self.show_own_camera_button.Disable()
        h_sizer3.Add(self.show_own_camera_button, 0, wx.LEFT, 20)
        h_sizer3.AddStretchSpacer()
        self.main_sizer.Add(h_sizer3, 0, wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_HORIZONTAL)

    def change_voice_chat_name(self, group_name):
        self.title_text.SetLabel("Voice Chat: " + group_name)

    def leave_voice_chat(self, event):
        wx.GetApp().client.leave_voice_chat()

    def toggle_mute(self, e):
        wx.GetApp().client.voice_chat.voice_chat_client.toggle_voice_share()
        if wx.GetApp().client.voice_chat.voice_chat_client.sending_voice_data:
            self.mute_button.SetBackgroundColour(wx.NullColour)
        else:
            self.mute_button.SetBackgroundColour(wx.GREEN)

    def toggle_camera(self, e):
        wx.GetApp().client.voice_chat.voice_chat_client.toggle_camera_share()
        if not wx.GetApp().client.voice_chat.voice_chat_client.sending_camera_data:
            self.camera_button.SetBackgroundColour(wx.NullColour)
            if self.own_camera_frame is not None:
                self.own_camera_frame.close_frame()
            self.show_own_camera_button.Disable()
        else:
            self.camera_button.SetBackgroundColour(wx.GREEN)
            self.show_own_camera_button.Enable()

    def toggle_screen_share(self, e):
        wx.GetApp().client.voice_chat.voice_chat_client.toggle_screen_share()
        if not wx.GetApp().client.voice_chat.voice_chat_client.sending_screen_data:
            self.screen_share_button.SetBackgroundColour(wx.NullColour)
        else:
            self.screen_share_button.SetBackgroundColour(wx.GREEN)

    def show_own_camera(self, e):
        if self.own_camera_frame is None:
            self.own_camera_frame = PictureDisplayFrame(self, OWN_CAMERA_FRAME_TYPE, title="your camera", size=DEFAULT_CAMERA_DISPLAY_SIZE)
            self.own_camera_frame.Show()
            self.show_own_camera_button.SetBackgroundColour((177, 255, 114))
        else:
            self.own_camera_frame.Restore()
            self.own_camera_frame.Raise()

    def close_own_camera_frame(self):
        if self.own_camera_frame is not None:
            self.own_camera_frame.close_frame()

    def set_own_camera_image(self, image_bytes):
        if self.own_camera_frame is not None:
            self.own_camera_frame.set_image(image_bytes)

    def change_participant_names_string(self, participant_names):
        participant_names_string = ""
        for name in participant_names:
            participant_names_string += name + ", "
        participant_names_string = participant_names_string[0:-2]  # delete last ", "
        self.participant_names_string = participant_names_string
        self.participants_text.SetLabel(VOICE_CHAT_PARTICIPANT_NAMES_TEXT.format(self.participant_names_string))
        self.Layout()

    def reset_buttons(self):
        self.mute_button.SetBackgroundColour(wx.NullColour)
        self.camera_button.SetBackgroundColour(wx.NullColour)
        self.screen_share_button.SetBackgroundColour(wx.NullColour)


class PictureDisplayFrame(wx.Frame):
    """
    A general frame that allows the displaying of images that change quickly.
    This panel uses double buffering in order to support quick changing of an image without
    flickering. It is used in order to show different data types that require changing images quickly,
    for example showing camera images or screen share images.
    """
    def __init__(self, parent, frame_type, id=wx.ID_ANY, title="Discord > Skype (?)", pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.MINIMIZE_BOX|wx.RESIZE_BORDER|wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.CLIP_CHILDREN, name=wx.FrameNameStr):
        super(PictureDisplayFrame, self).__init__(parent, id, title, pos, size, style, name)
        self.bitmap = None
        self.frame_type = frame_type
        self.Bind(wx.EVT_CLOSE, self.onClose, self)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda evt: None)
        self.SetMaxSize(size)

    def OnPaint(self, evt):
        if self.bitmap is not None:
            dc = wx.BufferedPaintDC(self)
            dc.Clear()
            dc.DrawBitmap(self.bitmap, 0, 0)

    def set_image(self, image_bytes):
        #image_bytes = self.get_resized_image_bytes(image_bytes)
        image_string = StringIO.StringIO(image_bytes)
        image_bitmap = wx.Image(image_string).ConvertToBitmap()
        self.bitmap = image_bitmap
        self.Refresh()

    def get_resized_image_bytes(self, image_bytes):  # not used right now
        image_save = BytesIO(image_bytes)
        image = Image.open(image_save)
        image = image.resize(self.GetSize(), Image.ANTIALIAS)
        image_save = BytesIO()
        image.save(image_save, format='jpeg')
        resized_image_bytes = image_save.getvalue()
        image.close()
        image_save.close()
        return resized_image_bytes

    def close_frame(self):
        if self.frame_type == CAMERA_FRAME_TYPE:
            self.GetParent().camera_frame = None
            self.GetParent().show_camera_button.SetBackgroundColour(wx.NullColour)
        elif self.frame_type == SCREEN_SHARE_FRAME_TYPE:
            self.GetParent().screen_frame = None
            self.GetParent().show_screen_share_button.SetBackgroundColour(wx.NullColour)
        elif self.frame_type == OWN_CAMERA_FRAME_TYPE:
            self.GetParent().own_camera_frame = None
            self.GetParent().show_own_camera_button.SetBackgroundColour(wx.NullColour)
        self.Destroy()

    def onClose(self, event):
        self.close_frame()