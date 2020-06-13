# -*- coding: utf-8 -*-
import wx
import os.path

"""
This script contains constants and classes which help the design and aesthetics of the GUI.
"""

NORMAL_FONT_SIZE = 14
TITLE_FONT_SIZE = 20
DEFAULT_LINE_DOWN_COORDINATES = (0, 40)
LOGIN_INPUT_SIZE = (200, 23)
SEARCH_USER_INPUT_SIZE = (250, 23)
DEFAULT_GAP = 10
SECONDARY_PANEL_LINE_DOWN_COORDINATES = (0, 5)
LISTBOX_HEIGHT = 230 #250
SEARCH_USER_RESULT_STRING = "Result for username: {0}"
SEARCH_USER_DOES_NOT_EXIST_STRING = "User doesn't exist"
SEARCH_USER_STATUS_TEXT = "User Status: {0}"
USER_INTERACTION_BUTTON_SIZE = (100, 30)
VOICE_CHAT_BUTTON_LABEL = "Current Voice Chat"
VOICE_CHAT_BUTTON_NAME = "CurrentVoiceChatButton"

CALL_DIALOG_SIZE = (300, 200)
CALLING_USER_TEXT = "Calling {0}..."
BEING_CALLED_BY_USERS_TEXT = "Being called by: {0}"
INVITED_TO_JOIN_CALL_TEXT = "Invited to join call: {0}"
VOICE_CHAT_PARTICIPANT_NAMES_TEXT = "Voice Chat Participants: {0}"
CHAT_MEMBERS_NAMES_TEXT = "Group Members: {0}"
CHAT_HOST_NAME_TEXT = "Host: {0}"
SECONDARY_PANEL_LENGTH = 250

PROFILE_PICTURE_SIZE = (160, 160)
DEFAULT_PROFILE_PICTURE_PATH = os.path.join("UserImages", "DefaultProfile.png")

PARTICIPANT_PANEL_SIZE = (200, 250)


class TitleStaticText(wx.StaticText):
    """
    A StaticText object with a constant font which should be used in all titles.
    """
    def __init__(self, parent, id=wx.ID_ANY, label="", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name=wx.StaticTextNameStr):
        super(TitleStaticText, self).__init__(parent, id, label, pos, size, style, name)
        title_font = wx.Font(TITLE_FONT_SIZE, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.SetFont(title_font)


class FontStaticText(wx.StaticText):
    """
    A StaticText object with a given font.
    """
    def __init__(self, parent, font, id=wx.ID_ANY, label="", pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name=wx.StaticTextNameStr):
        """
        :param font: wx.Font, the font of the text

        Constructs a new wx.StaticText object with a given font
        """
        super(FontStaticText, self).__init__(parent, id, label, pos, size, style, name)
        self.SetFont(font)


class NormalFont(wx.Font):
    """
    The default font of the program.
    """
    def __init__(self, pointSize=NORMAL_FONT_SIZE, family=wx.FONTFAMILY_DEFAULT, style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_NORMAL, underline=False, faceName="", encoding=wx.FONTENCODING_DEFAULT):
        super(NormalFont, self).__init__(pointSize, family, style, weight, underline, faceName, encoding)