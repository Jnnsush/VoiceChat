# -*- coding: utf-8 -*-

import socket
from select import select
import Common_Elements
from DataBaseHandler import *

IP = "0.0.0.0"
PORT = 9999

NEW_HOST_NAME_INDEX = 0

THIS_COMPUTER_IP = "192.168.1.238"

USER_ALREADY_BEING_CALLED_CALLING_ERROR = "Calling Error - The user is already being called right now."
CANNOT_CALL_EXISTING_PARTICIPANT_CALLING_ERROR = "Calling Error - Cannot call a user who is already a participant in the voice chat, and you cannot call yourself."

SENT_ADD_CONTACT_REQUEST_MESSAGE = "Successfully sent add contact request."
ALREADY_SENT_CONTACT_REQUEST_MESSAGE = "This user was already asked to be a contact or is already a contact."

#  -----------------------EXCEPTIONS--------------------#


class InvalidConnectionMessageException(Exception):
    pass


class UserIsNotCallHostException(Exception):
    pass


class CommunicationHandler(Common_Elements.BasicCommunicator):
    """
    This class is responsible for communication between server and clients.
    Contains functions that require sending and receiving information.
    """
    def __init__(self):
        """
        Constructs a CommunicationHandler object and its AESCipher object which
        allows it to encrypt and decrypt messages.
        """
        super(Common_Elements.BasicCommunicator, self).__init__()
        self.cipher = Common_Elements.AESCipher()  # prevent crash


    def relay_request_call_message(self, called_user, participant_names, call_group_name, host_name, not_in_call_members):
        """
        relays a request call message to the called user.
        :param called_user: User, the user who is being called
        :param participant_names:  [str], the names of the current voice chat participants
        """
        called_user.start_being_called(participant_names, call_group_name, host_name, not_in_call_members)
        called_by_message = Common_Elements.CalledByMessage(participant_names, call_group_name)
        self.send_full_message(called_user.client_socket, called_by_message)

    def send_call_rejected_message(self, called_user, actual_calling_user):
        """
        Informs calling users about a call reject via a CallRejectedMessage
        :param called_user: User, the user who is being called
        :param actual_calling_user: User, the user who actually started the call.
        """
        call_rejected_message = Common_Elements.CallRejectedMessage()
        self.send_full_message(actual_calling_user.client_socket, call_rejected_message)
        called_user.stop_being_called()

    def send_calling_failed_message(self, client_socket, error_message):
        """
        Inform a user about a failed calling attempt.
        :param client_socket: socket, the socket of the user who started calling
        :param error_message: str, the error message.
        """
        calling_failed_message = Common_Elements.CallingFailedMessage(error_message)
        self.send_full_message(client_socket, calling_failed_message)

    def send_invited_to_call_message(self, called_user, call_name, in_call_participants):
        """
        Informs the user about an invite to join a call when he is already a part of the call's group.
        :param called_user: User, the user who is invited to the call.
        :param call_name: str, the name of the call.
        :param in_call_participants: [str], the names of all the participants who are in the call.
        """
        invited_to_call_message = Common_Elements.InvitedToCallMessage(call_name, in_call_participants)
        self.send_full_message(called_user.client_socket, invited_to_call_message)

    def relay_call_join_request(self, call_name, group_host, requesting_username):
        """
        Sends a request to join an existing call by a call group member.
        :param call_name: str, the name of the call group.
        :param group_host: str, the name of the call host.
        :param requesting_username: str, the username of the requesting user
        """
        group_member_requested_join_message = Common_Elements.GroupMemberRequestedJoinMessage(call_name, requesting_username)
        self.send_full_message(group_host.client_socket, group_member_requested_join_message)

    def send_delete_call_group_message(self, call_name, other_group_members_users):
        """
        Sends a message to all group members except the one who sent this request that tells them to
        delete a call group. should be sent after the call has been ended.
        :param call_name: str, the name of the call group.
        :param other_group_members_users: [User], list of all the other users in the group, except the
        user who sent the request to delete the group call.
        """
        delete_call_group_message = Common_Elements.DeleteCallGroupMessage(call_name)
        self.broadcast_message_to_users_list(other_group_members_users, delete_call_group_message)

    def start_call_between_users(self, called_user, calling_users, not_in_call_members_users, database_access):
        """
        Sends both the calling users and the called users all the relevant information for them
        to start a call together.
        This includes both sending GroupMessages in order to tell the user to start a new group
        and CallMessages in order to allow the users to start a voice chat.
        :param called_user: User, the user who is being called
        :param calling_users: [User], the users who requested the call
        :param not_in_call_members_users: [User], the users who are in the group of the voice chat but
        not in the call itself.
        :param database_access: DataBaseHandler, access to the database object.
        """
        self.send_new_call_group_messages(called_user, calling_users + not_in_call_members_users)
        self.send_call_messages_for_call_start(called_user, calling_users, called_user.being_called_information.call_name, database_access)
        called_user.stop_being_called()

    def send_call_messages_for_call_start(self, called_user, calling_users, call_name, database_access):
        """
        Handles the sending of all CallMessage object to allow a new voice chat call.
        This function uniquely requires access to the database in order to send user pictures.
        :param called_user: User, the user who is being called.
        :param calling_users: [User], list of the calling users (the calling user and the users who are
        already in a call with him).
        :param call_name: str, the name of the call group that the voice chat belongs to.
        :param database_access: DataBaseHandler, access to the database object.
        """
        called_user_peers_list, calling_users_peers_dict = database_access.create_voice_chat_peers(called_user, calling_users)
        self.send_p2p_call_message_to_calling_users(calling_users_peers_dict, call_name)
        called_user_start_call_message = Common_Elements.StartNewCallMessage(called_user_peers_list, call_name)
        self.send_full_message(called_user.client_socket, called_user_start_call_message)

    def send_new_call_group_messages(self, called_user, in_group_users):
        """
        Handles the sending of all CallGroup messages that inform the users
        about the changes they need to do with their call groups.
        Note that a CreateCallGroupMessage will always be sent to the called user and will be sent to
        the calling user only if there is just one calling user (which means that he should also open a
        new call group).
        :param called_user: User, the user who is being called.
        :param in_group_users: [User], a list of all the users who are already in the call.
        """
        create_call_group_message = Common_Elements.CreateNewCallGroupMessage(called_user.being_called_information.call_name, called_user.being_called_information.host_name)
        self.send_full_message(called_user.client_socket, create_call_group_message)
        if len(in_group_users) == 1:  # only one caller, meaning a new call starts, should also create new group for the caller.
            self.send_full_message(in_group_users[0].client_socket, create_call_group_message)
        all_call_members_names = called_user.being_called_information.call_participants_names + called_user.being_called_information.not_in_call_members
        called_user_add_group_members_message = Common_Elements.AddCallGroupMembersMessage(called_user.being_called_information.call_name, all_call_members_names)
        self.send_full_message(called_user.client_socket, called_user_add_group_members_message)
        for in_group_user in in_group_users:
            in_group_user_add_group_members_message = Common_Elements.AddCallGroupMembersMessage(called_user.being_called_information.call_name, [called_user.username])
            self.send_full_message(in_group_user.client_socket, in_group_user_add_group_members_message)

    def send_p2p_call_message_to_calling_users(self, calling_users_peers_dict, call_name):
        """
        Handles the sending of all CallMessages to the calling users in order to
        let them start a call with the new participant.
        Also distinguishes between the need to start a completely new call or the need to just add
        a new participant to an already existing call.
        :param calling_users_peers_dict: {calling_user(User):VoiceChatPeer}, a dictionary that contains the calling
        users as keys and VoiceChatPeer objects of the called user as values.
        :param call_name: str, the name of the call group.
        """
        if len(calling_users_peers_dict) == 1:  # only one caller, should start new call
            calling_user = calling_users_peers_dict.keys()[0]
            calling_user_start_call_message = Common_Elements.StartNewCallMessage([calling_users_peers_dict[calling_user]], call_name)
            self.send_full_message(calling_user.client_socket, calling_user_start_call_message)
        else:  # multiple participants, should add new participant
            for calling_user in calling_users_peers_dict.keys():
                calling_user_add_participant_message = Common_Elements.AddParticipantToCallMessage(calling_users_peers_dict[calling_user], call_name)
                self.send_full_message(calling_user.client_socket, calling_user_add_participant_message)

    def send_change_host_message(self, call_name, new_host_name, all_group_members):
        """
        Sends a message to all group members that tells them to change the host of the group
        to a new host.
        :param call_name: str, the name of the call group.
        :param new_host_name: str, the name of the new host who is one of the participant.
        :param all_group_members: [User], a list of all call group members.
        :return:
        """
        change_host_message = Common_Elements.ChangeGroupHostMessage(call_name, new_host_name)
        self.broadcast_message_to_users_list(all_group_members, change_host_message)

    def send_remove_group_member_message(self, call_name, other_group_members_list, remove_username):
        """
        Instructs all group members to remove a user from the group.
        :param call_name: str, the name of the call group
        :param other_group_members_list: [User], a list of all the group members
        :param remove_username: str, the name of the user who should be removed.
        """
        remove_group_member_message = Common_Elements.RemoveGroupMemberMessage(call_name, remove_username)
        self.broadcast_message_to_users_list(other_group_members_list, remove_group_member_message)

    def send_successful_login_message(self, client_socket, user_contacts_info_list, user_pending_contacts_list, user_encoded_picture_bytes):
        """
        Informs a client about a successful login.
        :param client_socket: socket, the socket of the client who tried to log in
        :param user_contacts_info_list: [ContactInfo], a list of information objects about the user's contacts.
        :param user_pending_contacts_list: [str], a list of the user's pending users' names.
        :param user_encoded_picture_bytes: str, the user's profile picture encoded in base64.
        """
        successful_login_message = Common_Elements.SuccessfulLoginMessage(user_contacts_info_list, user_pending_contacts_list, user_encoded_picture_bytes)
        self.send_full_message(client_socket, successful_login_message)

    def send_login_failed_message(self, client_socket, message):
        """
        Informs a client about a failed login.
        :param client_socket: socket, the socket of the client who tried to log in
        :param message: str, the error message that will be shown to the client
        """
        failed_login_message = Common_Elements.LoginFailedMessage(message)
        self.send_full_message(client_socket, failed_login_message)

    def send_failed_register_message(self, client_socket, message):
        """
        Sends a message that informs a user about a failed register.
        :param client_socket: socket, the socket of the registering user.
        :param message: str, the error message.
        """
        register_failed_message = Common_Elements.RegisterFailedMessage(message)
        self.send_full_message(client_socket, register_failed_message)

    def send_successful_register_message(self, client_socket):
        """
        Sends a message that informs a user about a successful register.
        :param client_socket: socket, the socket of the registering user.
        """
        successful_register_message = Common_Elements.SuccessfulRegisterMessage()
        self.send_full_message(client_socket, successful_register_message)

    def send_stop_being_called_message(self, called_user):
        """
        Sends a message that informs a user that he is not being called anymore so
        his choice to accept / reject the call would do nothing.
        :param called_user: User, the user who is no longer being called.
        """
        stop_being_called_message = Common_Elements.StopBeingCalledMessage()
        self.send_full_message(called_user.client_socket, stop_being_called_message)
        called_user.stop_being_called()

    def send_user_information_message(self, requesting_user, username, does_exist, is_online, encoded_picture_bytes):
        """
        Sends the information about a user to a requesting user.
        :param requesting_user: User, the user who requested information.
        :param username: str, the user of the requested user.
        :param does_exist: Bool, True if said user exists, else False.
        :param is_online: Bool or None, True if said user is online, False if offline, or None if doesn't exist.
        """
        user_information_message = Common_Elements.UserInformationMessage(username, does_exist, is_online, encoded_picture_bytes)
        self.send_full_message(requesting_user.client_socket, user_information_message)

    def send_popup_message(self, client_socket, message):
        """
        Pop up a message for a specific user.
        :param client_socket: socket, the socket of the user
        :param message: str, the message that will be displayed to the user.
        """
        popup_message = Common_Elements.PopupMessage(message)
        self.send_full_message(client_socket, popup_message)

    def send_asked_to_be_contact_message(self, client_socket, asked_by_username):
        """
        Informs a user that another user asked to add him as a contact.
        :param client_socket: socket, the socket of the asked user.
        :param asked_by_username: str, the name of the asking user.
        """
        asked_to_be_contact_message = Common_Elements.AskedToBeContactMessage(asked_by_username)
        self.send_full_message(client_socket, asked_to_be_contact_message)

    def send_add_contacts_message(self, client_socket, contact_info_list):
        """
        Tells a user to add another user as a contact.
        :param client_socket: socket, the socket of the user.
        :param contact_info_list: [ContactInfo], a list of ContactInfo object which conatain information about
        the new contact.
        """
        add_contact_message = Common_Elements.AddContactsMessage(contact_info_list)
        self.send_full_message(client_socket, add_contact_message)

    def send_user_connected_message_to_all_contacts(self, connected_contacts_list, username):
        """
        Informs the contacts of a user that the user has connected to the server.
        :param connected_contacts_list: [User], a list of the user's contacts.
        :param username: str, the name of the connected user.
        """
        contact_connected_message = Common_Elements.ContactConnectedMessage(username)
        self.broadcast_message_to_users_list(connected_contacts_list, contact_connected_message)

    def send_user_went_offline_message_to_all_contacts(self, connected_contacts_list, username):
        """
        Informs the contacts of a user that the user has disconnected.
        :param connected_contacts_list: [User], a list of the user's contacts.
        :param username: str, the name of the connected user.
        """
        contact_went_offline_message = Common_Elements.ContactWentOfflineMessage(username)
        self.broadcast_message_to_users_list(connected_contacts_list, contact_went_offline_message)

    def broadcast_message_to_users_list(self, users_list, message):
        """
        Sends a message to a list of User objects.
        :param users_list: [User], list of users.
        :param message: Message, the message that needs to be sent.
        """
        for user in users_list:
            self.send_full_message(user.client_socket, message)

    def send_delete_contact_message(self, client_socket, contact_name):
        """
        Tells a user to delete a contact.
        :param client_socket: socket, the socket of the user.
        :param contact_name: str, the name of the contact.
        """
        delete_contact_message = Common_Elements.DeleteContactMessage(contact_name)
        self.send_full_message(client_socket, delete_contact_message)

    def send_contact_changed_picture_message_to_all_contacts(self, connected_contacts_list, username, encoded_picture_bytes):
        """
        Informs all contacts of a user that the user changed his profile picture.
        :param connected_contacts_list: [User], a list of the user's contacts.
        :param username: str, the name of the user.
        :param encoded_picture_bytes: str, the bytes of the new picture encoded in base64.
        """
        contact_changed_picture_message = Common_Elements.ContactChangedPictureMessage(username, encoded_picture_bytes)
        self.broadcast_message_to_users_list(connected_contacts_list, contact_changed_picture_message)

    def broadcast_participant_changed_picture_message(self, participants_list, username, encoded_picture_bytes):
        """
        Informs all participants of a user's voice chat that the user changed his profile picture.
        :param participants_list: [User], a list of the users who are in a voice chat with said user.
        :param username: str, the name of the user.
        :param encoded_picture_bytes: str, the bytes of the new picture encoded in base64.
        """
        participant_changed_picture_message = Common_Elements.ParticipantChangedPictureMessage(username, encoded_picture_bytes)
        self.broadcast_message_to_users_list(participants_list, participant_changed_picture_message)

    def relay_chat_text_message(self, chat_name, sender_username, send_time, message, receiving_users_list):
        """
        Relays a text chat message to all chat participants (aside from the sender).
        :param chat_name: str, the name of the chat.
        :param sender_username: str, the name of the sender.
        :param send_time: str, the send time of the message.
        :param message: str, the text message.
        :param receiving_users_list: [User], a list of the chat participants.
        """
        chat_text_message = Common_Elements.ChatTextMessage(chat_name, sender_username, send_time, message)
        self.broadcast_message_to_users_list(receiving_users_list, chat_text_message)

    def relay_chat_picture_message(self, chat_name, sender_username, send_time, encoded_picture_bytes, receiving_users_list):
        """
        Relays a picture chat message to all chat participants (aside from the sender).
        :param chat_name: str, the name of the chat.
        :param sender_username: str, the name of the sender.
        :param send_time: str, the send time of the message.
        :param encoded_picture_bytes: str, the bytes of the picture encoded in base64.
        :param receiving_users_list: [User], a list of the chat participants.
        """
        chat_picture_message = Common_Elements.ChatPictureMessage(chat_name, sender_username, send_time, encoded_picture_bytes)
        self.broadcast_message_to_users_list(receiving_users_list, chat_picture_message)


class Server(object):
    """
    This class represents the main Server of the voice chat program.
    The server as a whole is responsible for allowing the clients to start a p2p connection
    and sending relevant information to them.
    This specific class is responsible for interpreting and handling client requests and relaying them
    to the other Server components.
    """
    def __init__(self):
        """
        db - DataBaseHandler, the available database of the server.
        server_socket - socket, the server socket which accepts new clients.
        communication_handler - CommunicationHandler, the communication handler of the server.
        """
        self.db = DataBaseHandler()
        self.server_socket = socket.socket()
        self.communication_handler = CommunicationHandler()

    def open_server(self):
        """
        Binds the server to the constant address and opens it.
        """
        self.server_socket.bind((IP, PORT))
        self.server_socket.listen(1)

    def accept_pending_user(self):
        """
        Accepts a new pending user and adds it to the available database.
        *also lets the computer that runs the server to connect as a client.
        """
        client_socket, client_address = self.server_socket.accept()
        if client_address[ADDRESS_IP_INDEX] == "127.0.0.1":
            client_address = (THIS_COMPUTER_IP, client_address[ADDRESS_PORT_INDEX])
        self.db.pending_users[client_socket] = client_address
        print "DEBUG - new client accepted " + str(client_address)

    def disconnect_user(self, client_socket):
        """
        Disconnects the user from the server and informs his contacts about it.
        :param client_socket: socket, the socket of the client that needs to be disconnected.
        """
        try:
            disconnecting_user = self.db.connected_users[client_socket]
            connected_contacts_list = self.db.create_user_objects_list_of_connected_contacts(disconnecting_user.username)
            self.communication_handler.send_user_went_offline_message_to_all_contacts(connected_contacts_list, disconnecting_user.username)
        except (UserNotConnectedException, KeyError, socket.error) as e:
            print "ERROR IN USER DISCONNECT - " + str(type(e))
        self.db.disconnect_user(client_socket)

    def connect_user_to_server(self, client_socket, login_message):
        """
        Attempts to connect the user to the server and informs him about the result.
        :param client_socket: socket, the socket of the pending user that sent a login message.
        :param login_message: LoginMessage, the message that contains the user's login information
        """
        try:
            self.db.connect_user_to_server(client_socket, login_message)
            user_contacts_info_list = self.db.create_contacts_info_list(login_message.username)
            user_pending_contacts_list = self.db.create_pending_contacts_list(login_message.username)
            user_encoded_picture_bytes = self.db.get_user_encoded_picture_bytes(login_message.username)
            self.communication_handler.send_successful_login_message(client_socket, user_contacts_info_list, user_pending_contacts_list, user_encoded_picture_bytes)
            connected_contacts_list = self.db.create_user_objects_list_of_connected_contacts(login_message.username)
            self.communication_handler.send_user_connected_message_to_all_contacts(connected_contacts_list, login_message.username)
        except (IncorrectLoginInformationException, InvalidUserInformationException, UserAlreadyConnectedException) as e:
            self.communication_handler.send_login_failed_message(client_socket, e.get_message())

    def add_new_user_to_database(self, client_socket, register_message):
        """
        Adds a new user to the database when a client requests to register.
        Handles both outcomes of either a successful or a failed register.
        :param client_socket:
        :param register_message:
        :return:
        """
        try:
            self.db.add_new_user_to_database(register_message.username, register_message.password)
            self.communication_handler.send_successful_register_message(client_socket)
        except UserAlreadyExistsException as e:
            self.communication_handler.send_failed_register_message(client_socket, e.get_message())
        except InvalidUserInformationException as e:
            self.communication_handler.send_failed_register_message(client_socket, e.get_message())

    def handle_pending_user(self, client_socket):
        """
        Gets the message that a pending user sent and handles it (relays it to suitable functions).
        :param client_socket: socket, the socket of the pending user who sent data.
        """
        message = self.communication_handler.receive_full_message(client_socket)
        if isinstance(message, Common_Elements.LoginMessage):
            self.connect_user_to_server(client_socket, message)
        elif isinstance(message, Common_Elements.RegisterMessage):
            self.add_new_user_to_database(client_socket, message)
        else:
            raise InvalidConnectionMessageException()

    def handle_connected_user(self, client_socket):
        """
        Gets the message that a connected user sent and handles it (relays it to suitable functions).
        :param client_socket: socket, the socket of the connected user who sent data.
        :return:
        """
        message = self.communication_handler.receive_full_message(client_socket)
        print "DEBUG - " + str(message)
        try:
            if isinstance(message, Common_Elements.CallMessage):
                self.handle_call_messages(client_socket, message)
            elif isinstance(message, Common_Elements.NewOpenPortsMessage):
                self.db.connected_users[client_socket].add_new_open_p2p_ports(message.new_open_ports)
            elif isinstance(message, Common_Elements.CallGroupMessage):
                self.handle_call_group_messages(client_socket, message)
            elif isinstance(message, Common_Elements.ContactMessage):
                self.handle_contact_messages(client_socket, message)
            elif isinstance(message, Common_Elements.SendChatMessage):
                self.handle_chat_messages(client_socket, message)
            elif isinstance(message, Common_Elements.VoiceChatMessage):
                self.handle_voice_chat_messages(client_socket, message)
            elif isinstance(message, Common_Elements.RequestUserInformationMessage):
                self.provide_user_information(client_socket, message)
            elif isinstance(message, Common_Elements.ChangePictureMessage):
                self.change_user_picture(client_socket, message.encoded_picture_bytes, message.in_call_participants)
            elif isinstance(message, Common_Elements.DisconnectMessage):
                self.disconnect_user(client_socket)
        except UserNotConnectedException:
            print "DEBUG - USER NOT CONNECTED EXCEPTION"

    def handle_voice_chat_messages(self, client_socket, message):
        """
        Handles all messages that are a part of the voice chat between users.
        These messages are always general messages that inform other users in the call about something that
        happened in the voice chat. These messages are not raw data like voice data, screen share data, etc...
        :param client_socket: socket, the socket of the sending user.
        :param message: VoiceChatMessage, some kind of voice chat message.
        """
        sending_username = self.db.connected_users[client_socket].username
        participants_list = self.db.create_users_list_through_names(message.participants_names_list)
        ready_message = None
        if isinstance(message, Common_Elements.LeaveVoiceChatMessage):
            ready_message = Common_Elements.ParticipantLeaveVoiceChatMessage(sending_username)
        elif isinstance(message, Common_Elements.StartedCameraShareMessage):
            ready_message = Common_Elements.ParticipantStartedCameraShareMessage(sending_username)
        elif isinstance(message, Common_Elements.StoppedCameraShareMessage):
            ready_message = Common_Elements.ParticipantStoppedCameraShareMessage(sending_username)
        elif isinstance(message, Common_Elements.StartedScreenShareMessage):
            ready_message = Common_Elements.ParticipantStartedScreenShareMessage(sending_username)
        elif isinstance(message, Common_Elements.StoppedScreenShareMessage):
            ready_message = Common_Elements.ParticipantStoppedScreenShareMessage(sending_username)
        if ready_message is not None:
            self.communication_handler.broadcast_message_to_users_list(participants_list, ready_message)

    def handle_call_group_messages(self, client_socket, message):
        """
        Handles all the messages that have to do with Call Groups.
        :param client_socket: socket, the socket of the user who sent the message.
        :param message: GroupMessage, a group message object.
        :return:
        """
        try:
            if isinstance(message, Common_Elements.CommandMembersToCloseGroup):
                members_list = self.db.create_users_list_through_names(message.other_group_members_names)
                self.communication_handler.send_delete_call_group_message(message.call_name, members_list)
            elif isinstance(message, Common_Elements.HostLeftVoiceChatMessage):
                self.change_call_host(client_socket, message)
            elif isinstance(message, Common_Elements.LeaveGroupMessage):
                remove_username = self.db.connected_users[client_socket].username
                members_list = self.db.create_users_list_through_names(message.other_group_members_names)
                self.communication_handler.send_remove_group_member_message(message.call_name, members_list, remove_username)
        except UserIsNotCallHostException:
            pass

    def handle_call_messages(self, client_socket, message):
        """
        Handles all the messages that are part of the calling process.
        :param client_socket: socket, the socket of the user who sent the message
        :param message: CallMessage, a call message object
        """
        try:
            if isinstance(message, Common_Elements.RequestCallMessage):
                self.relay_request_call_message(client_socket, message)
            elif isinstance(message, Common_Elements.AcceptCallMessage):
                self.start_p2p_call(client_socket)
            elif isinstance(message, Common_Elements.RejectCallMessage):
                self.inform_user_about_call_reject(client_socket)
            elif isinstance(message, Common_Elements.StopCallingMessage):
                self.inform_user_about_call_stop(client_socket, message)
            elif isinstance(message, Common_Elements.RequestJoinCallMessage):
                self.relay_call_join_request(client_socket, message)
            elif isinstance(message, Common_Elements.AllowCallJoinMessage):
                self.allow_member_to_join_group_voice_chat(client_socket, message)
            elif isinstance(message, Common_Elements.UpdateUserBeingCalledInformationMessage):
                self.db.update_called_user_being_called_information(client_socket, message)
        except UserIsNotBeingCalledException:
            print "DEBUG - USER IS NOT BEING CALLED EXCEPTION"
        except UserAlreadyBeingCalledException:
            self.communication_handler.send_calling_failed_message(client_socket, USER_ALREADY_BEING_CALLED_CALLING_ERROR)
        except UserIsNotActualCallingUser:
            print "DEBUG - USER IS NOT ACTUAL CALLING USER EXCEPTION"

    def handle_contact_messages(self, client_socket, message):
        """
        Handles all messages that are a part of any contact process (Add contact, Delete contact, etc...)
        :param client_socket: socket, the socket of the sending user.
        :param message: ContactMessage, a ContactMessage object.
        """
        try:
            if isinstance(message, Common_Elements.RequestAddContactMessage):
                self.relay_request_add_contact_message(client_socket, message)
            elif isinstance(message, Common_Elements.AcceptContactMessage):
                self.allow_users_to_be_contacts(client_socket, message)
            elif isinstance(message, Common_Elements.RejectContactMessage):
                self.db.remove_user_pending_contact(self.db.connected_users[client_socket].username, message.reject_username)
            elif isinstance(message, Common_Elements.DeleteContactMessage):
                self.delete_user_contact(client_socket, message)
        except UserDoesNotExistException:
            pass

    def handle_chat_messages(self, client_socket, message):
        """
        Handles all messages that are connected to the written chats.
        :param client_socket: socket, the socket of the sending user.
        :param message: ChatMessage, a ChatMessage object, some kind of chat message.
        """
        sender_username = self.db.connected_users[client_socket].username
        receiving_users_list = self.db.create_users_list_through_names(message.chat_participants_list)
        if isinstance(message, Common_Elements.SendChatTextMessage):
            self.communication_handler.relay_chat_text_message(message.chat_name, sender_username, message.send_time, message.message, receiving_users_list)
        elif isinstance(message, Common_Elements.SendChatPictureMessage):
            self.communication_handler.relay_chat_picture_message(message.chat_name, sender_username, message.send_time, message.encoded_picture_bytes, receiving_users_list)

    def allow_users_to_be_contacts(self, accepting_client_socket, accept_contact_message):
        """
        Adds two users as contacts of each other after the contact adding process is over.
        Also removes them from the pending contacts list of each other.
        :param accepting_client_socket: socket, the socket of the client who accepted the friendship.
        :param accept_contact_message: AcceptContactMessage, the message that the accepting client sent.
        """
        accepting_user = self.db.connected_users[accepting_client_socket]
        self.db.remove_user_pending_contact(accepting_user.username, accept_contact_message.requesting_username)
        self.db.remove_user_pending_contact(accept_contact_message.requesting_username, accepting_user.username)
        self.db.add_user_contact(accepting_user.username, accept_contact_message.requesting_username)
        self.db.add_user_contact(accept_contact_message.requesting_username, accepting_user.username)
        is_requesting_user_connected = self.db.is_user_connected(accept_contact_message.requesting_username)
        if is_requesting_user_connected:
            requesting_user = self.db.find_connected_user_through_username(accept_contact_message.requesting_username)
            accepting_user_picture = self.db.get_user_encoded_picture_bytes(accepting_user.username)
            accepting_user_contact_info = [Common_Elements.ContactInfo(accepting_user.username, True, accepting_user_picture)]
            self.communication_handler.send_add_contacts_message(requesting_user.client_socket, accepting_user_contact_info)
        requesting_user_picture = self.db.get_user_encoded_picture_bytes(accept_contact_message.requesting_username)
        requesting_user_contact_info = [Common_Elements.ContactInfo(accept_contact_message.requesting_username, is_requesting_user_connected, requesting_user_picture)]
        self.communication_handler.send_add_contacts_message(accepting_user.client_socket, requesting_user_contact_info)

    def delete_user_contact(self, deleting_client_socket, delete_contact_message):
        """
        Deletes a contact of a user. Also deletes the sending user from the contacts list of the deleted
        contact and informs him if he is online.
        :param deleting_client_socket: socket, the socket of the client who sent the message.
        :param delete_contact_message: DeleteContactMessage, the message that the client sent.
        """
        deleting_user = self.db.connected_users[deleting_client_socket]
        self.db.remove_user_contact(deleting_user.username, delete_contact_message.contact_name)
        self.db.remove_user_contact(delete_contact_message.contact_name, deleting_user.username)
        try:
            deleted_user = self.db.find_connected_user_through_username(delete_contact_message.contact_name)
            self.communication_handler.send_delete_contact_message(deleted_user.client_socket, deleting_user.username)
        except UserNotConnectedException:
            pass

    def relay_request_add_contact_message(self, client_socket, request_add_contact_message):
        """
        Relays a request to add another user as a contact if the request is valid.
        The users must not already be contacts with each other, be pending contacts of each other, and the
        user can't send this request to himself.
        :param client_socket: socket, the socket of the requesting user.
        :param request_add_contact_message: RequestAddContactMessage, the message of the requesting user which
        contains the needed info.
        """
        requesting_user = self.db.connected_users[client_socket]
        if requesting_user.username != request_add_contact_message.request_username:  # you can't add yourself as a contact
            if not self.db.does_user_exist(request_add_contact_message.request_username):
                raise UserDoesNotExistException
            is_added = self.db.add_user_pending_contact(request_add_contact_message.request_username, requesting_user.username)
            if is_added:
                self.communication_handler.send_popup_message(client_socket, SENT_ADD_CONTACT_REQUEST_MESSAGE)
                try:
                    requested_user = self.db.find_connected_user_through_username(request_add_contact_message.request_username)
                    self.communication_handler.send_asked_to_be_contact_message(requested_user.client_socket, requesting_user.username)
                except UserNotConnectedException:
                    pass
            else:
                self.communication_handler.send_popup_message(client_socket, ALREADY_SENT_CONTACT_REQUEST_MESSAGE)

    def provide_user_information(self, client_socket, request_user_info_message):
        """
        Send a requesting user information about a specific user which he requested.
        :param client_socket: socket, the socket of the requesting user.
        :param request_user_info_message: RequestUserInformationMessage, the message that the
        requesting user sent.
        :return:
        """
        requesting_user = self.db.connected_users[client_socket]
        questioned_user_info = self.db.get_user_info_from_db(request_user_info_message.username)
        if questioned_user_info is None:
            self.communication_handler.send_user_information_message(requesting_user, request_user_info_message.username, False, None, None)
        else:
            is_online = self.db.is_user_connected(request_user_info_message.username)
            user_encoded_picture_bytes = self.db.get_user_encoded_picture_bytes(request_user_info_message.username)
            self.communication_handler.send_user_information_message(requesting_user, request_user_info_message.username, True, is_online, user_encoded_picture_bytes)

    def change_user_picture(self, client_socket, new_encoded_picture_bytes, in_call_participants):
        """
        Changes the user's picture and updates it for all online contacts and users he is in call with.
        :param client_socket: socket, the socket of the user.
        :param new_encoded_picture_bytes: str, the new picture bytes encoded in base64.
        :param in_call_participants: [str], the names of the participants who are in call with the user.
        """
        user = self.db.connected_users[client_socket]
        self.db.update_user_profile_picture(user.username, new_encoded_picture_bytes)
        connected_contacts_list = self.db.create_user_objects_list_of_connected_contacts(user.username)
        self.communication_handler.send_contact_changed_picture_message_to_all_contacts(connected_contacts_list, user.username, new_encoded_picture_bytes)
        if in_call_participants is not None:
            participants_list = self.db.create_users_list_through_names(in_call_participants)
            self.communication_handler.broadcast_participant_changed_picture_message(participants_list, user.username, new_encoded_picture_bytes)

    def change_call_host(self, host_client_socket, host_left_message):
        """
        Tells all the members of a certain group to change the group host to a different participant.
        This function is called when the host of a call group exists the call and thus a new host needs to be
        chosen. The new host is picked in this function.
        :param host_client_socket: socket, the socket of the user who sent the message, who should be the host.
        :param host_left_message:
        :return:
        """
        if self.db.connected_users[host_client_socket].username != host_left_message.host_name:
            raise UserIsNotCallHostException()
        members_list = self.db.create_users_list_through_names(host_left_message.other_group_members_names)
        members_list.append(self.db.connected_users[host_client_socket])
        new_host_name = host_left_message.other_participants_names[NEW_HOST_NAME_INDEX]  # takes a constant index as the new host
        self.communication_handler.send_change_host_message(host_left_message.call_name, new_host_name, members_list)

    def allow_member_to_join_group_voice_chat(self, group_host_client_socket, allow_call_join_message):
        """
        Allows a user to join an existing call.
        This function should be called after a group host got a request to add an existing member to the voice chat
        and thus sent a message containing the current voice chat information to allow him to join.
        :param group_host_client_socket: socket, the socket of the group host, the one who sent this message.
        :param allow_call_join_message: AllowCallJoinMessage, the message that the group host sent in order
        to allow the requesting user to join.
        """
        requesting_user = self.db.find_connected_user_through_username(allow_call_join_message.requesting_username)
        if requesting_user.is_being_called():
            self.inform_user_about_call_reject(requesting_user.client_socket)
        requesting_user.stop_being_called()
        host_user = self.db.connected_users[group_host_client_socket]
        other_in_call_participants = self.db.create_users_list_through_names(allow_call_join_message.other_participants_names)
        all_call_participants = other_in_call_participants + [host_user]
        # represent the requesting user as the called user and the in call members as the calling users
        self.communication_handler.send_call_messages_for_call_start(requesting_user, all_call_participants, allow_call_join_message.call_name, self.db)

    def relay_call_join_request(self, requesting_client_socket, request_join_call_message):
        """
        Relays a request to join an existing call by an existing call group member.
        :param requesting_client_socket: socket, the socket of the requesting client.
        :param request_join_call_message: RequestJoinCallMessage, the message that the requesting client sent
        that contains relevant information for allowing him to join.
        """
        group_host = self.db.find_connected_user_through_username(request_join_call_message.host_name)
        requesting_username = self.db.connected_users[requesting_client_socket].username
        self.communication_handler.relay_call_join_request(request_join_call_message.call_name, group_host, requesting_username)

    def inform_user_about_call_stop(self, sending_socket, stop_calling_message):
        """
        Informs a user about the fact that he is no longer being called.
        :param sending_socket: socket, the socket of the user who sent the message.
        :param stop_calling_message: StopCallingMessage, the message sent by the calling user that indicates that
        he is no longer calling the called user.
        """
        called_user = self.db.find_connected_user_through_username(stop_calling_message.stop_calling_username)
        if not called_user.is_being_called():
            raise UserIsNotBeingCalledException()
        if called_user.get_actual_calling_username() == self.db.connected_users[sending_socket].username:
            self.communication_handler.send_stop_being_called_message(called_user)

    def start_p2p_call(self, called_user_client_socket):
        """
        Starts a p2p call after the calling process is finished.
        :param called_user_client_socket: socket, the socket of the called user.
        """
        called_user = self.db.connected_users[called_user_client_socket]
        if not called_user.is_being_called():
            raise UserIsNotBeingCalledException()
        calling_users = self.db.create_calling_users_list(called_user)
        not_in_call_members_users = self.db.create_not_in_call_members_users_list(called_user)
        self.communication_handler.start_call_between_users(called_user, calling_users, not_in_call_members_users, self.db)

    def inform_user_about_call_reject(self, called_user_client_socket):
        """
        Informs all the calling users about the rejection of the call.
        :param called_user_client_socket: socket, the socket of the called user.
        """
        called_user = self.db.connected_users[called_user_client_socket]
        if not called_user.is_being_called():
            raise UserIsNotBeingCalledException()
        actual_calling_user = self.db.find_connected_user_through_username(called_user.get_actual_calling_username())
        self.communication_handler.send_call_rejected_message(called_user, actual_calling_user)

    def relay_request_call_message(self, caller_client_socket, request_call_message):
        """
        Relays the call request to the called user.
        :param caller_client_socket: socket, the socket of the first calling user (who requested the call himself).
        :param request_call_message: RequestCallMessage, the message that requests the call.
        """
        called_user = self.db.find_connected_user_through_username(request_call_message.call_username)
        if called_user.is_being_called():
            raise UserAlreadyBeingCalledException()
        caller_username = self.db.connected_users[caller_client_socket].username
        participant_names = request_call_message.other_participants_names + [caller_username]
        if called_user.username in participant_names:
            self.communication_handler.send_calling_failed_message(caller_client_socket, CANNOT_CALL_EXISTING_PARTICIPANT_CALLING_ERROR)
        elif called_user.username in request_call_message.not_in_call_members:
            called_user.start_being_called(participant_names, request_call_message.call_group_name, request_call_message.host_name, request_call_message.not_in_call_members)
            self.communication_handler.send_invited_to_call_message(called_user, request_call_message.call_group_name, participant_names)
        else:
            self.communication_handler.relay_request_call_message(called_user, participant_names, request_call_message.call_group_name, request_call_message.host_name, request_call_message.not_in_call_members)

    def run_server(self):
        """
        Runs the server by continuously accepting new clients, receiving data
        from users and sending it to a suitable function for handling.
        """
        try:
            while True:
                rlist, wlist, xlist = select(self.db.pending_users.keys() + self.db.connected_users.keys() + [self.server_socket], [], [])
                for ready_socket in rlist:
                    try:
                        if ready_socket is self.server_socket:
                            self.accept_pending_user()
                        elif ready_socket in self.db.pending_users:
                            self.handle_pending_user(ready_socket)
                        else:  # a connected user
                            self.handle_connected_user(ready_socket)
                    except socket.error:
                        self.disconnect_user(ready_socket)
                    except InvalidConnectionMessageException:
                        self.disconnect_user(ready_socket)
        finally:
            self.server_socket.close()
            self.db.conn.close()


def main():
    """
    Main fucntion. Runs the server to the end of times.
    Rest In Spaghetti CPU never forggeti :^(
    """
    server = Server()
    server.open_server()
    server.run_server()


if __name__ == '__main__':
    main()
