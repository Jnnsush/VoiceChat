
import wx
from Wx_Design_Objects import *
from Common_Elements import InputValidator

INVALID_USER_INFO_MESSAGE = "Invalid user information. Please enter valid username and password"


class InvalidUserInformationException(Exception):
    def get_message(self):
        return INVALID_USER_INFO_MESSAGE


class LoginFrame(wx.Frame):
    """
    The Login frame.
    The first frame that the user sees when he opens the program.
    after the user logs in this frame will close and the main program frame will open instead.
    Contains only one panel.
    """
    def __init__(self, parent, id=wx.ID_ANY, title="", pos=wx.DefaultPosition, size=(700, 550), style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER ^ wx.MAXIMIZE_BOX, name="LoginFrame"):
        super(LoginFrame, self).__init__(parent, id, title, pos, size, style, name)
        self.panel = LoginPanel(self)


class LoginPanel(wx.Panel):
    """
    The login panel which contains the user input and the buttons which allow
    the users to login or register to the server.
    """
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr):
        super(LoginPanel, self).__init__(parent, id, pos, size, style, name)
        self.SetBackgroundColour(wx.LIGHT_GREY)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.init_UI()
        self.SetSizer(self.main_sizer)

    def init_UI(self):
        title_text = TitleStaticText(self, label="Login To VShare", style=wx.ALIGN_CENTER)
        self.main_sizer.Add(title_text, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL, 20)
        self.main_sizer.Add(DEFAULT_LINE_DOWN_COORDINATES)  # Line Down
        # Username part
        h_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        username_text = FontStaticText(self, font=NormalFont(), style=wx.EXPAND, label="Username:")
        h_sizer1.Add((100, 0))
        h_sizer1.Add(username_text, 0)
        h_sizer1.Add((DEFAULT_GAP, 0))
        self.username_input = wx.TextCtrl(self, size=LOGIN_INPUT_SIZE)
        h_sizer1.Add(self.username_input, 0)
        self.main_sizer.Add(h_sizer1, 0, wx.ALL | wx.EXPAND)
        self.main_sizer.Add(DEFAULT_LINE_DOWN_COORDINATES)  # Line Down
        # Password part
        h_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer2.Add((100, 0))
        password_text = FontStaticText(self, font=NormalFont(), style=wx.EXPAND, label="Password:")
        h_sizer2.Add(password_text, 0)
        h_sizer2.Add((DEFAULT_GAP, 0))
        self.password_input = wx.TextCtrl(self, size=LOGIN_INPUT_SIZE, style=wx.TE_PASSWORD)
        h_sizer2.Add(self.password_input, 0)
        self.main_sizer.Add(h_sizer2, 0, wx.ALL | wx.EXPAND)
        self.main_sizer.Add(DEFAULT_LINE_DOWN_COORDINATES)
        # Buttons part
        h_sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.login_button = wx.Button(self, label="Login")
        self.Bind(wx.EVT_BUTTON, self.login, self.login_button)
        h_sizer3.AddStretchSpacer()
        h_sizer3.Add(self.login_button)
        h_sizer3.Add((DEFAULT_GAP * 3, 0))
        self.register_button = wx.Button(self, label="Register")
        self.Bind(wx.EVT_BUTTON, self.register, self.register_button)
        h_sizer3.Add(self.register_button)
        h_sizer3.AddStretchSpacer()
        self.main_sizer.Add(h_sizer3, 0, wx.ALL | wx.EXPAND | wx.ALIGN_CENTER_HORIZONTAL)
        # Server response text part
        h_sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        self.error_text = FontStaticText(self, font=NormalFont(), label="", style=wx.ALIGN_CENTER)
        self.error_text.SetForegroundColour(wx.RED)
        h_sizer4.Add(self.error_text)
        self.main_sizer.Add(h_sizer4, 0, wx.EXPAND | wx.TOP | wx.LEFT | wx.ALIGN_CENTER_HORIZONTAL, 20)
        # User info instructions
        self.main_sizer.Add((0, 20))
        h_sizer5 = wx.BoxSizer(wx.HORIZONTAL)
        username_instructions_text = FontStaticText(self, font=NormalFont(), label="Username has to be between 3 and 16 characters", style=wx.ALIGN_CENTER)
        username_instructions_text.SetForegroundColour(wx.BLUE)
        h_sizer5.Add(username_instructions_text)
        self.main_sizer.Add(h_sizer5, 0, wx.EXPAND | wx.TOP | wx.LEFT, 20)

        h_sizer6 = wx.BoxSizer(wx.HORIZONTAL)
        password_instructions_text = FontStaticText(self, font=NormalFont(), label="Password has to be between 3 and 16 characters", style=wx.ALIGN_CENTER)
        password_instructions_text.SetForegroundColour(wx.BLUE)
        h_sizer6.Add(password_instructions_text)
        self.main_sizer.Add(h_sizer6, 0, wx.EXPAND | wx.TOP | wx.LEFT, 20)

        h_sizer7 = wx.BoxSizer(wx.HORIZONTAL)
        allowed_characters_text = FontStaticText(self, font=NormalFont(), label="Allowed characters are upper and lower letters, digits and underscore", style=wx.ALIGN_CENTER)
        allowed_characters_text.SetForegroundColour(wx.BLUE)
        h_sizer7.Add(allowed_characters_text)
        self.main_sizer.Add(h_sizer7, 0, wx.EXPAND | wx.TOP | wx.LEFT, 20)

    def login(self, event):
        try:
            username = self.username_input.GetValue()
            password = self.password_input.GetValue()
            self.validate_login_input(username, password)
            print "DEBUG - connecting to server"
            wx.GetApp().client.login_to_server(username, password)
        except InvalidUserInformationException as e:
            self.display_error_message(e.get_message())

    def register(self, event):
        try:
            username = self.username_input.GetValue()
            password = self.password_input.GetValue()
            self.validate_login_input(username, password)
            print "DEBUG - trying to register to the server"
            wx.GetApp().client.register_as_new_user(username, password)
        except InvalidUserInformationException as e:
            self.display_error_message(e.get_message())

    def display_error_message(self, message):
        self.error_text.SetLabel(message)

    def validate_login_input(self, username, password):
        if not InputValidator.validate_username(username):
            raise InvalidUserInformationException()
        elif not InputValidator.validate_password(password):
            raise InvalidUserInformationException()
