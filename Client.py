# -*- coding: utf-8 -*-

import socket
import Common_Elements
from Voice_Chat import VoiceChat
from threading import Thread
import base64
import wx


SERVER_IP = "127.0.0.1"
PORT = 9999

DEFAULT_GROUP_CALL_NAME_TEMPLATE = "{0} -> {1}"


class GroupCallDoesNotExistException(Exception):
    pass


class UserIsNotInCallGroupException(Exception):
    pass


class ChatDoesNotExistException(Exception):
    pass


class CommunicationHandler(Common_Elements.BasicCommunicator):
    """
    Handles communication between the main server and the client.
    Contains all functions that need to send or receive information from the server.
    """
    def __init__(self):
        """
        client_socket - socket, the socket that connects the server and the client.
        the socket is automatically connecting to the constant server on initiation.

        the function also starts the AESCipher which allows the CommunicationHandler to encrypt/decrypt messages.
        """
        super(Common_Elements.BasicCommunicator, self).__init__()
        self.client_socket = socket.socket()
        self.client_socket.connect((SERVER_IP, PORT))
        self.cipher = Common_Elements.AESCipher()  # prevent crash

    def send_message(self, message):
        """
        Sends a message through the client socket
        :param message: Message, the message that needs to be sent
        """
        self.send_full_message(self.client_socket, message)

    def close_communication(self):
        """
        Sends a message to the server that informs about the closing of the communication and
        closes the socket.
        """
        disconnect_message = Common_Elements.DisconnectMessage()
        self.send_message(disconnect_message)
        self.client_socket.close()

    def request_start_call(self, call_username, other_participants_names, call_group_name, host_name, not_in_call_members):
        """
        Requests the server to start a call with the given username.
        :param call_username: str, the name of the user that the client wants to call
        :param other_participants_names: [str], the names of all the participants in the current voice chat.
        """
        request_call_message = Common_Elements.RequestCallMessage(call_username, other_participants_names, call_group_name, host_name, not_in_call_members)
        self.send_message(request_call_message)
        print "DEBUG - requested call from " + call_username

    def send_update_user_call_information(self, called_username, new_other_participants_names, new_call_group_name, new_host_name, new_not_in_call_members):
        """
        Requests the server to update the call information of the user that this user is currently calling.
        :param called_username: str, the name of the called user.
        :param new_other_participants_names: [str], the names of the current voice chat participants.
        :param new_call_group_name: str, the name of the call group.
        :param new_host_name: str, the name of the call host.
        :param new_not_in_call_members: [str], the names of the group members who are not in the voice chat itself.
        """
        update_user_being_called_information_message = Common_Elements.UpdateUserBeingCalledInformationMessage(
            called_username, new_other_participants_names, new_call_group_name, new_host_name, new_not_in_call_members)
        self.send_message(update_user_being_called_information_message)

    def request_join_call(self, call_group_name, host_name):
        """
        Requests the server to join a call which this client is already a part of its call group.
        :param call_group_name: str, the name of the call group.
        :param host_name: str, the name of the host of the call.
        """
        request_join_call_message = Common_Elements.RequestJoinCallMessage(call_group_name, host_name)
        self.send_message(request_join_call_message)

    def send_allow_call_join_message(self, call_name, requesting_username, other_in_call_participants_names):
        """
        Sends the server a message that allows a group member who is not in the voice chat to join the current voice chat.
        :param call_name: str, the name of the call group.
        :param requesting_username: str, the name of the user who requested to join the call.
        :param other_in_call_participants_names: [str], names of all the other participants who are in the voice chat.
        :return:
        """
        allow_call_join_message = Common_Elements.AllowCallJoinMessage(call_name, requesting_username, other_in_call_participants_names)
        self.send_message(allow_call_join_message)

    def accept_current_call(self):
        """
        Accepts the last call that the user got.
        This function will only be summoned after the user got a CalledByMessage.
        """
        accept_call_message = Common_Elements.AcceptCallMessage()
        self.send_message(accept_call_message)
        print "DEBUG - accepted call"

    def reject_current_call(self):
        """
        Rejects the last call that the user got.
        This function will only be summoned after the user got a CalledByMessage.
        """
        reject_call_message = Common_Elements.RejectCallMessage()
        self.send_message(reject_call_message)

    def send_new_open_ports_message(self, new_open_ports):
        """
        Informs the server about new open ports.
        :param new_open_ports: [ports], a list of newly open ports.
        """
        new_open_ports_message = Common_Elements.NewOpenPortsMessage(new_open_ports)
        self.send_message(new_open_ports_message)

    def send_close_call_group_message(self, call_name, other_group_members_names):
        """
        Sends a message that informs all other participants in a call group that
        the voice chat of that group is over and thus the group needs to be closed.
        :param call_name: str, the name of the call group.
        :param other_group_members_names: [str], names of all the other group members.
        """
        command_members_to_close_group_message = Common_Elements.CommandMembersToCloseGroup(call_name, other_group_members_names)
        self.send_message(command_members_to_close_group_message)

    def send_host_left_message(self, call_name, other_participants_names, other_group_members_names, current_host_name):
        """
        Sends a message to inform the server that the host has left and thus all other
        participants should change the host.
        :param call_name: str, the name of the call group.
        :param other_participants_names: [str], the names of all other participants in the voice chat.
        :param other_group_members_names: [str], the names of all group members who are not in the voice chat.
        :param current_host_name: [str], the name of the current host.
        """
        host_left_message = Common_Elements.HostLeftVoiceChatMessage(call_name, other_participants_names, other_group_members_names, current_host_name)
        self.send_message(host_left_message)

    def send_leave_group_message(self, call_name, other_group_members_names):
        leave_group_message = Common_Elements.LeaveGroupMessage(call_name, other_group_members_names)
        self.send_message(leave_group_message)

    def attempt_logging_in(self, username, password):
        """
        Attempts to log into the server with the given username and password and returns
        the server response.
        :param username: str, the username.
        :param password: str, the password
        :return: SuccessfulLoginMessage or LoginFailedMessage, the response of the server to the
        login attempt (either successful or failed attempt).
        """
        login_message = Common_Elements.LoginMessage(username, password)
        self.send_message(login_message)
        response = self.receive_full_message(self.client_socket)  # waiting for answer from the server
        return response

    def attempt_register(self, username, password):
        """
        Attempts to register to the server with the given username and password.
        :param username: str, the username that the client wants to register.
        :param password: str, the password of the new user.
        :return: SuccessfulRegisterMessage ot RegisterFailedMessage, the response of the server
        to the register attempt (either successful or failed attempt).
        """
        register_message = Common_Elements.RegisterMessage(username, password)
        self.send_message(register_message)
        response = self.receive_full_message(self.client_socket)
        return response

    def stop_calling_user(self, username):
        """
        Send a user a message that tells him that this client stopped calling him through the server.
        :param username: str, the name of the user who stopped being called.
        """
        stop_calling_message = Common_Elements.StopCallingMessage(username)
        self.send_message(stop_calling_message)

    def ask_for_user_information(self, username):
        """
        Sends a message to the server that asks to get the information about a specific user.
        :param username: str, the username of the user.
        """
        request_user_info_message = Common_Elements.RequestUserInformationMessage(username)
        self.send_message(request_user_info_message)

    def request_add_contact(self, username):
        """
        Requests the server to add a contact.
        :param username: str, the name of the user who needs to be asked to be a contact.
        """
        request_add_contact_message = Common_Elements.RequestAddContactMessage(username)
        self.send_message(request_add_contact_message)

    def accept_contact(self, username):
        """
        Accepts a contact request.
        :param username: str, the name of the user who asked to be contacts.
        """
        accept_contact_message = Common_Elements.AcceptContactMessage(username)
        self.send_message(accept_contact_message)

    def reject_contact(self, username):
        """
        Rejects a contact request.
        :param username: str, the name of the user who asked to be contacts.
        """
        reject_contact_message = Common_Elements.RejectContactMessage(username)
        self.send_message(reject_contact_message)

    def request_delete_contact(self, contact_name):
        """
        Requests the server to delete a contact.
        :param contact_name: str, the name of the contact.
        """
        delete_contact_message = Common_Elements.DeleteContactMessage(contact_name)
        self.send_message(delete_contact_message)

    def send_change_picture_message(self, encoded_picture_bytes, in_call_participants):
        """
        Asks the server to change the user's profile picture.
        :param encoded_picture_bytes: str, the bytes of the new picture encoded in base64.
        :param in_call_participants: [str], names of the participants in the current voice chat.
        """
        change_picture_message = Common_Elements.ChangePictureMessage(encoded_picture_bytes, in_call_participants)
        self.send_message(change_picture_message)

    def send_chat_text_message(self, chat_name, chat_participants_list, send_time, message):
        """
        Sends a text message to a given chat.
        :param chat_name: str, name of the chat.
        :param chat_participants_list: [str], names of the chat participants.
        :param send_time: str, sending time.
        :param message: str, the text message.
        """
        send_chat_text_message = Common_Elements.SendChatTextMessage(chat_name, chat_participants_list, send_time, message)
        self.send_message(send_chat_text_message)

    def send_chat_picture_message(self, chat_name, chat_participants_list, send_time, encoded_picture_bytes):
        """
        Sends a picture message to a given chat.
        :param chat_name: str, name of the chat.
        :param chat_participants_list: [str], names of the chat participants.
        :param send_time: str, sending time.
        :param encoded_picture_bytes: str, the bytes of the picture encoded in base64.
        """
        send_chat_picture_message = Common_Elements.SendChatPictureMessage(chat_name, chat_participants_list, send_time, encoded_picture_bytes)
        self.send_message(send_chat_picture_message)


class MainClient(object):
    """
    This class represents the client of the main server.
    It is responsible for handling messages from the server and running
    the voice chat.
    """
    def __init__(self):
        """
        *communication_handler - CommunicationHandler, the communication handler of the client
        *username - str, the username of the client. Starts as None until the client logs in.
        *receive_thread - Thread, the thread the receives data from the server. Starts as None until the client logs in.
        *voice_chat - VoiceChat, the voice chat that the user participates in currently.
        Is None if the user is not in a voice chat.
        *name_call_group_dict - {call_name: ActiveCallGroup}, a dictionary that contains call names as keys
        and the CallGroup objects as values.
        *calling_username - str or None - name of the user who is currently being called by this client, or None
        if the client is not calling anyone right now.
        """
        self.communication_handler = CommunicationHandler()
        self.username = None
        self.calling_username = None
        self.receive_thread = None
        self.voice_chat = None
        self.name_call_group_dict = {}  # {call_name: ActiveCallGroup}
        self.username_contact_dict = {}

    def is_in_call(self):
        """
        Tells whether the client is in a voice chat right now.
        :return: True if the user participates in a voice chat, else False.
        """
        return self.voice_chat is not None

    def is_calling_other_user(self):
        """
        Tells whether the client is currently calling another user.
        :return: True if the user is currently calling another user, else False.
        """
        return self.calling_username is not None

    def login_to_server(self, username, password):
        """
        Attempts to login to the server and handles the server's response.
        :param username: str, the name that the client entered.
        :param password: str, the password that the client entered.
        """
        server_response = self.communication_handler.attempt_logging_in(username, password)
        if isinstance(server_response, Common_Elements.SuccessfulLoginMessage):
            self.username = username
            self.receive_thread = Thread(target=self.receive_from_server)
            self.receive_thread.start()
            wx.GetApp().switch_to_main_program_frame()
            user_picture_bytes = base64.b64decode(server_response.user_encoded_picture_bytes)
            wx.CallAfter(wx.GetApp().program_frame.secondary_panel.set_profile_picture, user_picture_bytes)
            self.add_pending_contacts(server_response.pending_contacts_list)
            self.add_contacts(server_response.contacts_info_list)
        elif isinstance(server_response, Common_Elements.LoginFailedMessage):
            wx.CallAfter(wx.GetApp().login_frame.panel.display_error_message, server_response.message)

    def register_as_new_user(self, username, password):
        """
        Registers to the server as a new user.
        :param username: str, the username to register.
        :param password: str, the new user's password.
        """
        server_response = self.communication_handler.attempt_register(username, password)
        if isinstance(server_response, Common_Elements.SuccessfulRegisterMessage):
            self.login_to_server(username, password)
            wx.CallAfter(wx.GetApp().inform_about_successful_register)
        elif isinstance(server_response, Common_Elements.RegisterFailedMessage):
            wx.CallAfter(wx.GetApp().login_frame.panel.display_error_message, server_response.message)

    def request_start_call(self, call_username):
        """
        Requests the server to start a call with the given username.
        if this client is already in a call invites the given username to the current call.
        :param call_username: str, the name of the user that the client wants to call
        """
        if self.is_in_call():
            self.invite_user_to_current_call(call_username)
        else:
            new_call_name = self.get_new_group_call_name(call_username)
            self.communication_handler.request_start_call(call_username, [], new_call_name, self.username, [])

    def invite_user_to_current_call(self, call_username):
        """
        Invites a user to the current voice chat the this client is in.
        :param call_username: str, the name of the user to invite to the call.
        """
        current_call_participants_names = [participant.username for participant in self.voice_chat.participants]
        current_call_group = self.name_call_group_dict[self.voice_chat.active_call_group_name]
        not_in_call_members = [name for name in current_call_group.other_group_members_names if name not in current_call_participants_names]
        self.communication_handler.request_start_call(call_username, current_call_participants_names, current_call_group.call_name, current_call_group.host_name, not_in_call_members)

    def update_called_user_information(self):
        """
        Requests the server to update the BeingCalledInformation of the user who is currently being called by this user
        (if the client is currently calling another user).
        """
        if self.is_calling_other_user():
            print self.is_in_call()
            if self.is_in_call():
                current_call_participants_names = [participant.username for participant in self.voice_chat.participants]
                current_call_group = self.name_call_group_dict[self.voice_chat.active_call_group_name]
                not_in_call_members = [name for name in current_call_group.other_group_members_names if name not in current_call_participants_names]
                self.communication_handler.send_update_user_call_information(self.calling_username, current_call_participants_names, current_call_group.call_name, current_call_group.host_name, not_in_call_members)
            else:
                wx.CallAfter(wx.GetApp().stop_calling)

    def join_group_voice_chat(self, active_group_name):
        """
        Tries to join the voice chat of a group that this user is already in it as a group member.
        :param active_group_name: str, the name of the call group.
        """
        host_name = self.name_call_group_dict[active_group_name].host_name
        self.communication_handler.request_join_call(active_group_name, host_name)

    def allow_group_member_to_join_voice_chat(self, call_name, requesting_user_name):
        """
        Allows a group member to join the voice chat of the group.
        Should be only called when this user is in the group's voice chat himself.
        :param call_name: str, the name of the call group.
        :param requesting_user_name: str, the name of the user who requested to join.
        """
        if call_name not in self.name_call_group_dict:
            raise GroupCallDoesNotExistException()
        active_group = self.name_call_group_dict[call_name]
        if not active_group.is_user_in_group(requesting_user_name):
            raise UserIsNotInCallGroupException
        in_call_participants_names = [participant.username for participant in self.voice_chat.participants]
        if self.is_in_call():
            self.communication_handler.send_allow_call_join_message(call_name, requesting_user_name, in_call_participants_names)

    def get_new_group_call_name(self, call_username):  # call name: "{this username} -> {called username} {""/1/2...}"
        """
        Creates a new call name.
        A call name has a template: "{this username} -> {called username} {""/1/2...}"
        this template ensures that no two calls have can have the same name.
        :param call_username: str, the username that this user wants to call.
        """
        new_call_name = DEFAULT_GROUP_CALL_NAME_TEMPLATE.format(self.username, call_username)
        try_number = 1
        while new_call_name in self.name_call_group_dict.keys():
            new_call_name = DEFAULT_GROUP_CALL_NAME_TEMPLATE.format(self.username, call_username) + " ({0})".format(str(try_number))
            try_number += 1
        return new_call_name

    def receive_from_server(self):
        """
        Continuously receives data from the server, interprets it and sends it to be handled
        in a suitable function.
        """
        while True:
            try:
                message = self.communication_handler.receive_full_message(self.communication_handler.client_socket)
                if isinstance(message, Common_Elements.CallMessage):
                    self.handle_call_messages(message)
                elif isinstance(message, Common_Elements.CallGroupMessage):
                    self.handle_call_group_messages(message)
                elif isinstance(message, Common_Elements.ContactMessage):
                    self.handle_contact_messages(message)
                elif isinstance(message, Common_Elements.DisplayableChatMessage):
                    self.handle_chat_messages(message)
                elif isinstance(message, Common_Elements.ParticipantVoiceChatMessage) and self.is_in_call():
                    self.voice_chat.voice_chat_server.handle_pickled_voice_chat_messages(message)
                elif isinstance(message, Common_Elements.UserInformationMessage):
                    wx.CallAfter(wx.GetApp().program_frame.main_panel.home_page_panel.display_user_information, message.username, message.does_exist, message.is_online, message.encoded_picture_bytes)
                elif isinstance(message, Common_Elements.PopupMessage):
                    wx.CallAfter(wx.GetApp().pop_up_message, message.message)
            except socket.error:
                pass
            except GroupCallDoesNotExistException:
                print "DEBUG - group call was not found"

    def handle_chat_messages(self, message):
        """
        Handles all messages that have to do with a written chat, for example displaying chat messages.
        :param message: ChatMessage, the message that was sent by the server.
        """
        try:
            chat_panel = self.get_chat_panel(message.chat_name)
            wx.CallAfter(wx.GetApp().program_frame.secondary_panel.emphasize_message, chat_panel, message.chat_name)
            if isinstance(message, Common_Elements.ChatTextMessage):
                wx.CallAfter(chat_panel.chat.display_message, message.sender_username, message.send_time, message.message)
            elif isinstance(message, Common_Elements.ChatPictureMessage):
                picture_bytes = base64.b64decode(message.encoded_picture_bytes)
                wx.CallAfter(chat_panel.chat.display_picture, message.sender_username, message.send_time, picture_bytes)
        except ChatDoesNotExistException:
            pass

    def get_chat_panel(self, chat_name):
        """
        Gets a chat panel, either the panel that contains the chat of a group or the panel that contains the
        chat of two contacts (part of the GUI).
        :param chat_name: str, the name of the chat.
        :return: ContactChatPanel or GroupChatPanel - the panel that contains the written chat.
        """
        if chat_name in self.username_contact_dict:
            return wx.GetApp().program_frame.contact_name_chat_panel_dict[chat_name]
        elif chat_name in self.name_call_group_dict:
            return wx.GetApp().program_frame.group_name_chat_panel_dict[chat_name]
        raise ChatDoesNotExistException

    def handle_contact_messages(self, message):
        """
        Handles all messages that have to do with contacts and the contact adding process.
        :param message: ContactMessage, the message that the server sent.
        """
        if isinstance(message, Common_Elements.AskedToBeContactMessage):
            self.add_pending_contacts([message.asked_by_username])
        elif isinstance(message, Common_Elements.AddContactsMessage):
            self.add_contacts(message.contacts_info_list)
        elif isinstance(message, Common_Elements.ContactConnectedMessage):
            wx.CallAfter(wx.GetApp().program_frame.contact_name_chat_panel_dict[message.contact_name].contact_connected)
        elif isinstance(message, Common_Elements.ContactWentOfflineMessage):
            wx.CallAfter(wx.GetApp().program_frame.contact_name_chat_panel_dict[message.contact_name].contact_went_offline)
        elif isinstance(message, Common_Elements.ContactChangedPictureMessage):
            self.username_contact_dict[message.contact_name].change_contact_picture(message.encoded_picture_bytes)
        elif isinstance(message, Common_Elements.DeleteContactMessage):
            self.delete_contact(message.contact_name)

    def add_pending_contacts(self, contact_names_list):
        """
        Adds pending contacts to the pending contacts list in the GUI.
        :param contact_names_list: [str], names of the pending contacts to add.
        """
        for contact_name in contact_names_list:
            wx.CallAfter(wx.GetApp().program_frame.secondary_panel.add_choice_to_pending_contacts_listbox, contact_name)
            print "DEBUG - added new Pending contact " + contact_name

    def add_contacts(self, contacts_info_list):
        """
        Adds contacts to the clients contacts list and updates them in the GUI.
        :param contacts_info_list: [ContactInfo], a list of objects that contain information about the new contacts.
        """
        for contact_info in contacts_info_list:
            contact_picture_bytes = base64.b64decode(contact_info.encoded_picture_bytes)
            self.username_contact_dict[contact_info.contact_name] = Contact(contact_info.contact_name, contact_info.is_connected, contact_picture_bytes)
            wx.CallAfter(wx.GetApp().program_frame.add_new_contact_chat, self.username_contact_dict[contact_info.contact_name])
            wx.CallAfter(wx.GetApp().program_frame.secondary_panel.delete_choice_from_pending_contact_listbox, contact_info.contact_name)
            print "DEBUG - added new contact " + contact_info.contact_name + " and deleted him from pending users."

    def delete_contact(self, contact_name):
        """
        Deletes a contact from the clients contacts list and updates it in the GUI.
        :param contact_name: str, name of the contact that needs to be removed.
        """
        if contact_name in self.username_contact_dict:
            wx.CallAfter(wx.GetApp().program_frame.destroy_contact_chat_panel, contact_name)
            del self.username_contact_dict[contact_name]

    def handle_call_group_messages(self, message):
        """
        Handles all messages that have to do with the user's current active groups.
        :param message: GroupMessage, the message that the server sent.
        """
        if isinstance(message, Common_Elements.CreateNewCallGroupMessage):
            self.create_new_call_group(message.call_name, message.host_name)
        # Existing Groups Functions
        if message.call_name not in self.name_call_group_dict:
            raise GroupCallDoesNotExistException()
        try:
            if isinstance(message, Common_Elements.AddCallGroupMembersMessage):
                self.name_call_group_dict[message.call_name].add_members(message.members_names)
            elif isinstance(message, Common_Elements.DeleteCallGroupMessage):
                self.delete_call_group(message.call_name)
            elif isinstance(message, Common_Elements.ChangeGroupHostMessage):
                self.name_call_group_dict[message.call_name].change_host(message.new_host_name)
                self.update_called_user_information()
                print "DEBUG - host changed to - " + self.name_call_group_dict[message.call_name].host_name
            elif isinstance(message, Common_Elements.RemoveGroupMemberMessage):
                self.remove_group_member(message.call_name, message.remove_username)
                self.update_called_user_information()
        except KeyError:
            print "ERROR - Group not found"

    def handle_call_messages(self, message):
        """
        Handles all messages that are part of the calling process.
        :param message: CallMessage, the message that the server sent.
        """
        try:
            if isinstance(message, Common_Elements.CalledByMessage):
                wx.CallAfter(wx.GetApp().show_being_called_dialog, message.called_by_names)
            elif isinstance(message, Common_Elements.InvitedToCallMessage):
                wx.CallAfter(wx.GetApp().show_invited_to_call_dialog, message.call_name, message.in_call_participants)
            elif isinstance(message, Common_Elements.StartNewCallMessage):
                self.start_new_voice_chat(message)
            elif isinstance(message, Common_Elements.AddParticipantToCallMessage):
                self.add_participant_to_voice_chat(message.voice_chat_peer, message.active_call_group_name)
                self.update_called_user_information()
            elif isinstance(message, Common_Elements.CallRejectedMessage):
                wx.CallAfter(wx.GetApp().cancel_calling_dialog)
            elif isinstance(message, Common_Elements.CallingFailedMessage):
                wx.CallAfter(wx.GetApp().cancel_calling_dialog, message.error_message)
            elif isinstance(message, Common_Elements.StopBeingCalledMessage):
                wx.CallAfter(wx.GetApp().cancel_being_called_dialog)
            elif isinstance(message, Common_Elements.GroupMemberRequestedJoinMessage):
                self.allow_group_member_to_join_voice_chat(message.call_name, message.requesting_username)
            elif isinstance(message, Common_Elements.ParticipantChangedPictureMessage):
                self.change_in_call_participant_picture(message.participant_username, message.encoded_picture_bytes)
        except GroupCallDoesNotExistException:
            pass
        except UserIsNotInCallGroupException:
            pass

    def change_in_call_participant_picture(self, participant_username, new_encoded_picture_bytes):
        """
        changes the picture of a voice chat participant in the GUI.
        :param participant_username: str, the name of the participant.
        :param new_encoded_picture_bytes: str, the bytes of the picture encoded in base64.
        """
        if self.is_in_call() and participant_username in self.voice_chat.voice_chat_client.get_participants_names_list():
            wx.CallAfter(wx.GetApp().program_frame.main_panel.current_voice_chat_panel.participant_viewer.set_participant_picture, participant_username, new_encoded_picture_bytes)

    def start_new_voice_chat(self, start_call_message):
        """
        Starts the voice chat according to the message sent by the server.
        :param start_call_message: StartCallMessage, the message that contains relevant information to start a call.
        :return:
        """
        if self.is_in_call():
            self.leave_voice_chat()
        wx.CallAfter(wx.GetApp().enable_voice_chat_gui, start_call_message.active_call_group_name)
        self.voice_chat = VoiceChat(self, start_call_message.active_call_group_name)
        print "peers list: " + str(start_call_message.voice_chat_peers_list) + " call name: " + start_call_message.active_call_group_name
        for voice_chat_peer in start_call_message.voice_chat_peers_list:
            self.add_participant_to_voice_chat(voice_chat_peer, start_call_message.active_call_group_name)
        self.voice_chat.start_sending_data()
        wx.CallAfter(wx.GetApp().program_frame.disable_join_call_button_for_all_chats)

    def leave_voice_chat(self):
        """
        Fully leaves the current voice chat.
        """
        still_in_call_participants = [participant.username for participant in self.voice_chat.participants]
        self.voice_chat.leave_call()
        self.close_voice_chat(still_in_call_participants)

    def close_voice_chat(self, still_in_call_participants=None):
        """
        Closes the current VoiceChat object and handles the GUI.
        Also sends all other group members a message that tells them to delete the group if the voice
        chat has ended, or sends the server a message that tells it to choose a different host if
        this user was the call host.
        """
        wx.CallAfter(wx.GetApp().disable_voice_chat_gui)
        self.voice_chat.voice_chat_client.is_in_call = False
        try:
            active_call_group = self.name_call_group_dict[self.voice_chat.active_call_group_name]
            if not self.voice_chat.participants:  # if no one is left then the call group should be ended
                self.communication_handler.send_close_call_group_message(active_call_group.call_name, active_call_group.other_group_members_names)
                self.delete_call_group(active_call_group.call_name)
            elif self.username == active_call_group.host_name:
                self.communication_handler.send_host_left_message(active_call_group.call_name, still_in_call_participants, active_call_group.other_group_members_names, active_call_group.host_name)
        except KeyError:
            print "##NOTE## - group {" + str(self.voice_chat.active_call_group_name) + "} not found - groups list: " + str(self.name_call_group_dict.keys())
        wx.CallAfter(wx.GetApp().program_frame.enable_join_call_button_for_all_chats)
        self.voice_chat = None
        print "DEBUG - CURRENT VOICE CHAT CLOSED"

    def create_new_call_group(self, call_name, host_name):
        """
        Creates a new call group and stores it in the User's data.
        :param call_name: str, the name of the new call group.
        :param host_name: str, the name of the host of the group.
        """
        self.name_call_group_dict[call_name] = ActiveCallGroup(call_name, host_name)
        wx.CallAfter(wx.GetApp().program_frame.add_new_group_chat, self.name_call_group_dict[call_name])

    def delete_call_group(self, call_name):
        """
        Deletes a call group and handles its GUI
        :param call_name: str, the name of the call group.
        """
        if call_name in self.name_call_group_dict:
            wx.CallAfter(wx.GetApp().program_frame.destroy_group_chat_panel, self.name_call_group_dict[call_name])
            del self.name_call_group_dict[call_name]

    def leave_call_group(self, call_name):
        """
        Leaves a call group and deletes it.
        :param call_name: str, the name of the call.
        """
        if call_name in self.name_call_group_dict:
            if self.is_in_call():
                if self.voice_chat.active_call_group_name == call_name:
                    self.leave_voice_chat()
            if call_name in self.name_call_group_dict:  # if group still exist after exiting voice chat
                self.communication_handler.send_leave_group_message(call_name, self.name_call_group_dict[call_name].other_group_members_names)
                self.delete_call_group(call_name)

    def remove_group_member(self, call_name, remove_username):
        """
        Removes a member from a call group.
        :param call_name: str, the name of the call.
        :param remove_username: str, the name of the user that needs to be removed.
        """
        if call_name in self.name_call_group_dict:
            self.name_call_group_dict[call_name].remove_member_from_group(remove_username)
            if self.name_call_group_dict[call_name].is_group_empty():
                self.delete_call_group(call_name)

    def add_participant_to_voice_chat(self, voice_chat_peer, active_call_group_name):
        """
        Adds participants to the current voice chat according to a list of p2p peers.
        :param voice_chat_peer: [Peer], a list of peers with relevant information for connection.
        :param active_call_group_name: str, the name of the voice chat's call group.
        """
        if self.voice_chat is not None and self.voice_chat.active_call_group_name == active_call_group_name:
            peer = voice_chat_peer
            self.voice_chat.add_participant(peer.username, peer.ip, peer.voice_ports_pair, peer.screen_ports_pair, peer.camera_ports_pair)
            participant_picture_bytes = base64.b64decode(peer.peer_encoded_picture_bytes)
            wx.CallAfter(wx.GetApp().program_frame.main_panel.current_voice_chat_panel.participant_viewer.add_participant_panel, peer.username, participant_picture_bytes)
            if peer.username == self.calling_username:
                wx.CallAfter(wx.GetApp().destroy_call_dialog)
            print "DEBUG - STARTED CALL WITH " + peer.username  # + " sending info to: " + str((peer.ip, peer.send_to_port)) + " receiving from port: " + str(peer.receive_port)

    def close_client(self):
        """
        Fully closes the client by closing the connection with the main server
        and closing the voice chat.
        """
        if self.is_in_call():
            self.leave_voice_chat()
        call_group_names_list = self.name_call_group_dict.keys()[:]
        for call_group_name in call_group_names_list:
            self.leave_call_group(call_group_name)
        self.communication_handler.close_communication()


class ChatHostObject(object):
    """
    Declares an object as a chat host, which means that each instance of the object has a chat attached
    to it.
    """
    def get_chat_name(self):
        """
        gets the name of the chat.
        :return: str, the name of the chat.
        """
        pass

    def get_chat_participants_list(self):
        """
        gets the chat participants names, aside from this client.
        :return: [str], a list of the chat participants names.
        """
        pass


class ActiveCallGroup(ChatHostObject):
    def __init__(self, call_name, host_name):
        """
        call_name - the name of the group
        group_members_names - the names of all the members in the group, including this user
        host_name - the name of the current host. a 'host' is a user that is connected to the chat and he is
        publicly known to all other call members in the chat as the host. when an unconnected call member wants
        to join the voice chat of the group, he will call the host, as the host is ALWAYS present in the voice
        chat itself. when the host leaves the voice chat, another user will be chosen as the new host.

        :param call_name: str, the name of the group
        :param host_name: str, the name of the host, starts as the group creator.
        """
        self.call_name = call_name
        self.other_group_members_names = []
        self.host_name = host_name  # The host starts as the call creator
        print "DEBUG - started new call group named: " + self.call_name + " host: " + self.host_name

    def add_members(self, username_list):
        """
        Adds members to the group members list.
        :param username_list: [str], a list of new members names.
        """
        self.other_group_members_names.extend(username_list)
        wx.CallAfter(wx.GetApp().program_frame.update_group_chat_panel, self.call_name)
        print "DEBUG - added members " + str(username_list) + " to call group: " + self.call_name

    def change_host(self, new_host_name):
        """
        Changes the host of the call group.
        :param new_host_name: str, the name of the new host of the group.
        """
        self.host_name = new_host_name
        wx.CallAfter(wx.GetApp().program_frame.update_group_chat_panel, self.call_name)

    def is_user_in_group(self, username):
        """
        Tells if a user is in the group or not.
        :param username: str, the username that needs to be checked.
        :return: Bool, True if the given username is in the call group or else False.
        """
        return username in self.other_group_members_names

    def remove_member_from_group(self, username):
        """
        Removes a member from the group.
        :param username: str, the name of the group member that needs to be removed.
        """
        if self.is_user_in_group(username):
            self.other_group_members_names.remove(username)
            wx.CallAfter(wx.GetApp().program_frame.update_group_chat_panel, self.call_name)
            print "DEBUG - removed member " + str(username) + " from call group: " + self.call_name

    def is_group_empty(self):
        """
        Tells whether a group is empty or not.
        :return: True if the group is empty, else False.
        """
        return len(self.other_group_members_names) == 0

    def get_group_members_names_string(self):
        """
        returns a string of the group members names.
        :return: str, a string that contains the call group's members names split by commas.
        """
        group_members_names_string = ""
        for name in self.other_group_members_names:
            group_members_names_string += name + ", "
        group_members_names_string = group_members_names_string[0:-2]  # delete last ", "
        return group_members_names_string

    def get_chat_name(self):
        """
        Returns the chat name, which is the same as the call name.
        :return: str, the chat name.
        """
        return self.call_name

    def get_chat_participants_list(self):
        """
        Returns the chat participants, which is all the group members.
        :return: [str], the chat participants.
        """
        return self.other_group_members_names


class Contact(ChatHostObject):
    def __init__(self, username, is_connected, picture_bytes):
        """
        Constructs a Contact object.
        :param username: str, the contact's name.
        :param is_connected: Bool, is the contact connected to the server currently.
        :param picture_bytes: bytes, the bytes of the contact's profile picture.
        """
        self.username = username
        self.is_connected = is_connected
        self.picture_bytes = picture_bytes

    def change_contact_picture(self, new_encoded_picture_bytes):
        """
        Changes the contact's picture.
        :param new_encoded_picture_bytes: the bytes of the new picture encoded in base64.
        """
        self.picture_bytes = base64.b64decode(new_encoded_picture_bytes)
        wx.CallAfter(wx.GetApp().program_frame.contact_name_chat_panel_dict[self.username].change_contact_picture, self.picture_bytes)

    def get_chat_name(self):
        """
        Returns the chat name from the contact's perspective, which is this client's name.
        :return: str, the chat's name.
        """
        return wx.GetApp().client.username  # the other contact will see the chat name as this client's name

    def get_chat_participants_list(self):
        """
        Returns the chat participant from the client's perspective, which is only the contact.
        :return: [str], the chat participants.
        """
        return [self.username]



