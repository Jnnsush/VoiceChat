
import pyaudio
import socket
from threading import Thread
import Queue
import numpy as np
import cv2
from io import BytesIO
from PIL import Image, ImageGrab
import time
import audioop
import math
from Common_Elements import ParticipantStoppedScreenShareMessage, ParticipantStoppedCameraShareMessage, ParticipantStartedCameraShareMessage, \
    ParticipantStartedScreenShareMessage, ParticipantLeaveVoiceChatMessage, LeaveVoiceChatMessage, StartedScreenShareMessage, \
    StartedCameraShareMessage, StoppedScreenShareMessage, StoppedCameraShareMessage
from Common_Elements import AESCipher
import wx

SERVER_IP = "0.0.0.0"
# SERVER_PORT = 6666
ADDRESS_IP_INDEX = 0
ADDRESS_PORT_INDEX = 1

# Communication Constants
VOICE_DATA_BYTES = 3000
CAMERA_DATA_BYTES = 65536
SCREEN_DATA_BYTES = 65536
MAX_QUEUE_DELAY = 20

# Camera/Screen Constants
MAX_PACKET_SIZE = 65000
FPS = 24
FPS_PERIOD_TIME = 1.0 / FPS
SCREEN_PICTURE_SIZE = (800, 600)
CAMERA_PICTURE_SIZE = (848, 480)
MAXIMUM_QUALITY = 100
MINIMUM_QUALITY = 45
QUALITY_CHANGE_RATE = 3
MIN_QUALITY_THRESHOLD = MINIMUM_QUALITY + QUALITY_CHANGE_RATE
MAX_QUALITY_THRESHOLD = MAXIMUM_QUALITY - QUALITY_CHANGE_RATE
HIGHER_QUALITY_SIGN_BYTES = 55000


# Audio Constants
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
MINIMUM_DECIBEL_VOLUME = 40
INDICATOR_SHOW_TIME = 0.2


#  ------------------DATA OBJECTS-----------------#
class ParticipantNotInCallException(Exception):
    pass


class UdpCommunicationHandler(object):
    """
    A UDP communication handler that fully handles the sending and receiving
    of data.
    """
    def __init__(self):
        """
        Constructs the CommunicationHandler and starts the AESCipher which allows it to encrypt/decrypt messages.
        """
        self.cipher = AESCipher()

    def broadcast_voice_data(self, sock, raw_voice_data, participants_list):
        """
        This function sends raw voice data to a list of participants.
        :param sock: socket, the socket that should send the data.
        :param raw_voice_data: str, the raw voice data as it was recorded by the microphone.
        :param participants_list: [Participant], a list of participants to send the data to.
        """
        for participant in participants_list:
            self.send_ready_message(sock, raw_voice_data, participant.voice_address)

    def broadcast_camera_data(self, sock, raw_camera_data, participants_list):
        """
        This function sends raw camera data to a list of participants.
        :param sock: socket, the socket that should send the data.
        :param raw_camera_data: str, the raw camera data.
        :param participants_list: [Participant], a list of participants to send the data to.
        """
        for participant in participants_list:
            self.send_ready_message(sock, raw_camera_data, participant.camera_address)

    def broadcast_screen_data(self, sock, raw_screen_data, participants_list):
        """
        This function sends raw screen data to a list of participants.
        :param sock: socket, the socket that should send the data.
        :param raw_screen_data: str, the raw screen data.
        :param participants_list: [Participant], a list of participants to send the data to.
        """
        for participant in participants_list:
            self.send_ready_message(sock, raw_screen_data, participant.screen_address)

    def send_ready_message(self, sock, ready_message, address):
        """
        The basic sending of data through a UDP socket.
        Is called to send every message part.
        :param sock: socket, the socket that sends the data.
        :param ready_message: str, data that needs to be sent, usually a single message part.
        :param address: (IP, PORT), the address to send the data to.
        """
        encrypted_message = self.cipher.encrypt_message(ready_message)
        sock.sendto(encrypted_message, address)

    def receive_udp_message(self, sock, bytes_num):
        """
        receives a UDP message with a constant amount of BYTES.
        :param sock: socket, the receiving socket
        :return: data - str, the message that the socket received
        address - the address of the sender (IP, PORT).
        """
        encrypted_data, address = sock.recvfrom(bytes_num)
        data = self.cipher.decrypt_message(encrypted_data)
        return data, address


class Participant(object):
    """
    This class represents a voice chat participant. It contains all
    the relevant information about a participant and the communication tools
    that connect the user with the participant.
    """
    def __init__(self, username, ip, receive_voice_stream, voice_ports_pair, screen_ports_pair, camera_ports_pair):
        """
        *username - str, the username of the participant.
        *receive_stream - the audio stream to which audio data from this user will be written.
        *is_in_call - Bool, True if the participant is still in the call, else False
        *process_thread - the thread that continuously reads data that this participant sent and handles it.
        *voice_queue -  Queue, a queue which contains the voice data that the receive thread receives and the process
        thread processes.
        *addresses - different addresses of the participant for different data types.
        *receive sockets - different receives sockets that receive different data types from the participant.
        *receive threads - threads that receive different data types from the participant and handles them.
        *voice_indication_thread - a thread that is responsible for indicating that the
        participant is speaking in the GUI.
        *indiciation_time - the time up until which the participant's picture needs to be emphasized
        (because he sent voice data)
        """
        self.username = username
        self.voice_address = (ip, voice_ports_pair.send_to_port)
        self.screen_address = (ip, screen_ports_pair.send_to_port)
        self.camera_address = (ip, camera_ports_pair.send_to_port)
        self.receive_voice_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.receive_screen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.receive_camera_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.open_receiving_sockets(voice_ports_pair, screen_ports_pair, camera_ports_pair)
        self.receive_voice_thread = None
        self.process_voice_thread = None
        self.camera_thread = None
        self.screen_thread = None
        self.voice_indication_thread = None
        self.receive_voice_stream = receive_voice_stream
        self.voice_queue = Queue.Queue()
        self.indication_time = 0
        self.is_in_call = True

    def open_receiving_sockets(self, voice_ports_pair, screen_ports_pair, camera_ports_pair):
        """
        Opens the receiving sockets of the different data types of the participant.
        :param voice_ports_pair: PortsPair, a pair of ports to send to and receive from voice data.
        :param screen_ports_pair: PortsPair, a pair of ports to send to and receive from screen data.
        :param camera_ports_pair: PortsPair, a pair of ports to send to and receive from camera data.
        """
        self.receive_voice_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # allows sockets to reuse the same ports.
        self.receive_voice_socket.bind((SERVER_IP, voice_ports_pair.receive_port))
        self.receive_screen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.receive_screen_socket.bind((SERVER_IP, screen_ports_pair.receive_port))
        self.receive_camera_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.receive_camera_socket.bind((SERVER_IP, camera_ports_pair.receive_port))

    def close_sockets(self):
        """
        Closes the participant's receiving sockets.
        """
        self.receive_voice_socket.close()
        self.receive_camera_socket.close()
        self.receive_screen_socket.close()

    def get_used_ports_list(self):
        """
        Gets the list of ports that this participant's receiving sockets use.
        :return: [int], a list of ports that the participant's sockets use.
        """
        used_ports_list = []
        used_ports_list.append(self.receive_voice_socket.getsockname()[ADDRESS_PORT_INDEX])
        used_ports_list.append(self.receive_screen_socket.getsockname()[ADDRESS_PORT_INDEX])
        used_ports_list.append(self.receive_camera_socket.getsockname()[ADDRESS_PORT_INDEX])
        return used_ports_list

    def clean_voice_queue(self):
        """
        Entirely cleans the data queue of the participant.
        Used in order to cancel delay and make the call "real-time" if it has been delayed.
        """
        print "BEFORE CLEAN - " + str(self.voice_queue.qsize())
        with self.voice_queue.mutex:
            self.voice_queue.queue.clear()
        print "DEBUG - DATA QUEUE CLEANED"


class VoiceChat(object):
    """
    This class represents a p2p voice chat.
    It contains the voice chat Client and Server.
    """
    def __init__(self, using_client, active_call_group_name):
        """
        *communication_handler - CommunicationHandler, the communication handler of the voice chat.
        *audio - pyaudio.Pyaudio() - used to create audio streams.
        *participants - list, a list of all Participant objects.
        *voice_chat_server - VoiceChatServer, the server part of the p2p connection.
        *voice_chat_client - VoiceChatClient, the client part of the p2p connection.
        *using_client - MainClient, the client who opened this VoiceChat object.
        *active_call_group_name - str, the name of the call group that this voice chat belongs to.
        """
        self.communication_handler = UdpCommunicationHandler()
        self.audio = pyaudio.PyAudio()
        self.participants = []  # [Participant]
        self.using_client = using_client
        self.voice_chat_server = VoiceChatServer(self.communication_handler, self.participants, self.using_client)
        self.voice_chat_client = VoiceChatClient(self.audio, self.communication_handler, self.participants, self.using_client)
        self.active_call_group_name = active_call_group_name

    def add_participant(self, username, ip, voice_ports_pair, screen_ports_pair, camera_ports_pair):
        """
        Adds a new participant to the voice chat.
        :param username: str, the participant's username.
        :param ip: str, the participant's ip.
        :param voice_ports_pair: PortsPair, a pair of ports to send to and receive from voice data.
        :param screen_ports_pair: PortsPair, a pair of ports to send to and receive from screen data.
        :param camera_ports_pair: PortsPair, a pair of ports to send to and receive from camera data.
        """
        receive_stream = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
        participant = Participant(username, ip, receive_stream, voice_ports_pair, screen_ports_pair, camera_ports_pair)
        self.participants.append(participant)
        self.voice_chat_server.start_participant_threads(participant)
        self.voice_chat_client.send_sharing_messages_to_new_participant(participant)
        wx.CallAfter(wx.GetApp().set_voice_chat_participants_names, self.voice_chat_server.get_participant_names_list())

    def leave_call(self):
        """
        Leaves the call entirely by informing everyone about leaving and then closing their connections.
        """
        self.voice_chat_client.broadcast_leave_call_message()
        self.voice_chat_client.client_socket.close()
        self.voice_chat_client.cap.release()
        self.voice_chat_server.stop_listening_to_all_participants()

    def start_sending_data(self):
        """
        Starts the thread that sends data to all participants.
        """
        send_voice_thread = Thread(target=self.voice_chat_client.send_voice_data)
        send_camera_thread = Thread(target=self.voice_chat_client.send_camera_data)
        send_screen_thread = Thread(target=self.voice_chat_client.send_screen_data)
        send_voice_thread.start()
        send_camera_thread.start()
        send_screen_thread.start()
        print "DEBUG - voice chat running"

    def is_user_in_call(self, username):
        """
        Tells whether a user is in this voice chat.
        :param username: str, the name of the user.
        :return: Bool, True if there is a user with the given username in the call, else False.
        """
        return username in self.voice_chat_client.get_participants_names_list()


class VoiceChatClient(object):
    """
    This class represents the Client of the p2p voice chat.
    Its responsible for sending data to all the participants.
    """
    def __init__(self, audio, communication_handler, participants, using_client):
        """
        *communication_handler - CommunicationHandler, the communication handler of the voice chat.
        (Same as the main VoiceChat)
        *participants - dict, a dictionary that contains the ip of the participants as keys
         and the Participant objects as values. (same as the main VoiceChat)
        *send_stream - the audio stream that gets audio input from the user.
        *client_socket - the socket that sends data to all the participants.
        *using_client - access to the main client object.
        *cap - allows us to take camera pictures.
        *sending_[x]_data - booleans that tell whether the user is currently sending some type of data.
        *is_in_call - Bool, tells whether the user is still in the call.
        *screen_share_quality - the current quality of screen images in percentages.
        """
        self.communication_handler = communication_handler
        self.send_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.participants = participants
        self.using_client = using_client
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_PICTURE_SIZE[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_PICTURE_SIZE[1])
        self.sending_voice_data = True
        self.sending_camera_data = False
        self.sending_screen_data = False
        self.is_in_call = True
        self.screen_share_quality = 76
        #---- TO ALLOW CONNECTION BETWEEN DIFFERENT NETWORKS (ONLY 1 COMPUTER PER NETWORK) 
        #self.client_socket.bind(("0.0.0.0", SERVER_PORT))
        #print "*** - OPENED CLINET SOCKET ON ADDRESS " + str(self.client_socket.getsockname())

    def get_participants_names_list(self):
        """
        Gets the names of the call participants.
        :return: [str], the names of the call participants.
        """
        return [participant.username for participant in self.participants]

    def toggle_voice_share(self):
        """
        Starts/Stops sending voice data.
        """
        self.sending_voice_data = not self.sending_voice_data

    def toggle_camera_share(self):
        """
        Starts/Stops sending camera data.
        :return:
        """
        self.sending_camera_data = not self.sending_camera_data
        if self.sending_camera_data:
            toggle_message = StartedCameraShareMessage(self.get_participants_names_list())
            #self.cap = cv2.VideoCapture(0)
            #self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 400)
            #self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 300)
        else:
            toggle_message = StoppedCameraShareMessage(self.get_participants_names_list())
            #self.cap.release()
        self.using_client.communication_handler.send_message(toggle_message)

    def toggle_screen_share(self):
        """
        Starts/Stops sending screen data.
        """
        self.sending_screen_data = not self.sending_screen_data
        if self.sending_screen_data:
            toggle_message = StartedScreenShareMessage(self.get_participants_names_list())
        else:
            toggle_message = StoppedScreenShareMessage(self.get_participants_names_list())
        self.using_client.communication_handler.send_message(toggle_message)

    def send_sharing_messages_to_new_participant(self, participant):
        """
        Informs a new participant that just joined the call about the sharing of camera or screen data.
        :param participant: Participant, the new participant.
        """
        if self.sending_camera_data:
            message = StartedCameraShareMessage([participant.username])
            self.using_client.communication_handler.send_message(message)
        if self.sending_screen_data:
            message = StartedScreenShareMessage([participant.username])
            self.using_client.communication_handler.send_message(message)

    def broadcast_voice_data(self, voice_data):
        """
        Sends voice data to all participants.
        :param voice_data: bytes, the raw voice data.
        """
        self.communication_handler.broadcast_voice_data(self.client_socket, voice_data, self.participants)

    def broadcast_camera_data(self, camera_data_bytes):
        """
        Sends camera data to all participants.
        :param camera_data_bytes: bytes, the raw camera data.
        """
        self.communication_handler.broadcast_camera_data(self.client_socket, camera_data_bytes, self.participants)

    def broadcast_screen_data(self, screen_data_bytes):
        """
        Sends screen data to all participants.
        :param screen_data_bytes: bytes, the raw screen data.
        """
        self.communication_handler.broadcast_screen_data(self.client_socket, screen_data_bytes, self.participants)

    def broadcast_leave_call_message(self):
        """
        Informs participants about leaving the call.
        """
        leave_call_message = LeaveVoiceChatMessage(self.get_participants_names_list())
        self.using_client.communication_handler.send_message(leave_call_message)

    def send_voice_data(self):
        """
        Continuously gets audio input from the user and sends it to all the participants after checking
        its loud enough to be considered speaking.
        """
        try:
            while self.is_in_call:
                if self.sending_voice_data:
                    data = self.send_stream.read(CHUNK)
                    rms = audioop.rms(data, 2)
                    decibel_volume = 0
                    if rms > 0:
                        decibel_volume = 20 * math.log10(rms)
                    if decibel_volume >= MINIMUM_DECIBEL_VOLUME:
                        self.broadcast_voice_data(data)
        except socket.error as e:
            print "send_voice_data error: " + str(e)
        finally:
            self.client_socket.close()

    def send_camera_data(self):
        """
        Continuously gets camera pictures from the user and sends them to all the participants after
        checking their size.
        """
        try:
            while self.is_in_call:
                if self.sending_camera_data:
                    try:
                        ret, frame = self.cap.read()
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        frame = cv2.flip(frame, 1)
                        image = Image.fromarray(frame)
                        frame_save = BytesIO()
                        image.save(frame_save, format='jpeg')
                        frame_bytes = frame_save.getvalue()
                        image.close()
                        if len(frame_bytes) <= 65000:
                            self.broadcast_camera_data(frame_bytes)
                            wx.CallAfter(wx.GetApp().program_frame.main_panel.current_voice_chat_panel.set_own_camera_image, frame_bytes)
                        time.sleep(FPS_PERIOD_TIME)
                    except cv2.error as e:
                        pass  # print "SEND CAMERA ERROR - " + str(e)
        except socket.error as e:
            print e
        finally:
            self.cap.release()
            self.client_socket.close()

    def send_screen_data(self):
        """
        Continuously gets screenshots from the user and sends them to all the participants after
        checking their size. also handles their quality to allow as many screenshots as possible to
        be sent.
        """
        try:
            while self.is_in_call:
                if self.sending_screen_data:
                    screenshot = ImageGrab.grab()
                    screenshot = screenshot.resize(SCREEN_PICTURE_SIZE, Image.ANTIALIAS)
                    screenshot_save = BytesIO()
                    screenshot.save(screenshot_save, format="jpeg", optimize=True, quality=self.screen_share_quality)
                    screenshot_bytes = screenshot_save.getvalue()
                    self.handle_screen_share_quality(screenshot_bytes)
                    if len(screenshot_bytes) <= MAX_PACKET_SIZE:
                        self.broadcast_screen_data(screenshot_bytes)
                    time.sleep(FPS_PERIOD_TIME)
        except socket.error as e:
            print e
        finally:
            self.client_socket.close()

    def handle_screen_share_quality(self, screenshot_bytes):
        """
        Handles the screen share quality in order to make the screenshots small enough in
        size and maintain the best quality possible. The pictures size cannot be over 64kb and thus
        we need to dynamically change their quality in order to allow as many pictures as possible to be
        This function gets the current screenshot and changes the quality of the next screenshot according to it.
        sent through the socket.
        :param screenshot_bytes: bytes, the bytes of the screenshot.
        """
        if len(screenshot_bytes) < HIGHER_QUALITY_SIGN_BYTES and self.screen_share_quality <= MAX_QUALITY_THRESHOLD:
            self.screen_share_quality += QUALITY_CHANGE_RATE
        elif len(screenshot_bytes) > MAX_PACKET_SIZE:
            if self.screen_share_quality >= MIN_QUALITY_THRESHOLD:
                self.screen_share_quality -= QUALITY_CHANGE_RATE


class VoiceChatServer(object):
    """
    This class represents the server of the p2p voice chat.
    It is responsible for receiving data from the participants and handling it.
    """
    def __init__(self, communication_handler, participants, using_client):
        """
        *communication_handler - CommunicationHandler, the communication handler of the voice chat.
        (Same as the main VoiceChat)
        *participants - dict, a dictionary that contains the ip of the participants as keys
         and the Participant objects as values. (same as the main VoiceChat)
         *using_client - MainClient, the client that uses this voice chat object.
        """
        self.communication_handler = communication_handler
        self.participants = participants
        self.using_client = using_client

    def receive_voice_data(self, participant):
        """
        Continuously receive data from a given participant through its unique socket
        and puts the data in the data queue to let the process thread handle it.
        :param participant: Participant, the participant that the user should listen to.
        """
        try:
            while participant.is_in_call:
                try:
                    data, address = self.communication_handler.receive_udp_message(participant.receive_voice_socket, VOICE_DATA_BYTES)
                    participant.voice_queue.put(data)
                    participant.indication_time = time.time() + INDICATOR_SHOW_TIME
                    # print "DEBUG QUEUE START - " + str(participant.voice_queue.qsize())
                except socket.error as e:
                    print "VOICE DATA ERROR " + str(e)
        finally:
            participant.receive_voice_socket.close()

    def process_voice_data(self, participant):
        """
        Continuously reads data from the participant's data queue and handles the
        participants messages.
        If the data queue has a bigger delay than the constant max delay value, then the
        queue is cleared.
        :param participant: Participant, the participant whose messages the function handles.
        """
        while participant.is_in_call:
            voice_data = participant.voice_queue.get()
            participant.voice_queue.task_done()
            # print "DEBUG QUEUE STOP - " + str(participant.voice_queue.qsize())
            if participant.voice_queue.qsize() > MAX_QUEUE_DELAY:
                participant.clean_voice_queue()
            participant.receive_voice_stream.write(voice_data)

    def voice_indication_loop(self, participant):
        """
        Continuously checks whether the picture of the participant should be emphasized in the GUI.
        The picture is emphasized as long as the participant is sending voice data.
        :param participant: Participant, the participant that the function handles.
        """
        while participant.is_in_call:
            if time.time() < participant.indication_time:
                wx.CallAfter(wx.GetApp().program_frame.main_panel.current_voice_chat_panel.participant_viewer.emphasize_participant_panel, participant.username)
                while participant.is_in_call and time.time() < participant.indication_time:
                    pass
                wx.CallAfter(wx.GetApp().program_frame.main_panel.current_voice_chat_panel.participant_viewer.stop_participant_panel_emphasize, participant.username)

    def handle_pickled_voice_chat_messages(self, message):
        """
        Handles messages that were sent through the server instead of through the usual P2P connection.
        These messages are general messages that contain some kind of command, and not raw data like that data
        that is sent in P2P connection.
        :param message:
        :return:
        """
        try:
            participant = self.find_participant_through_username(message.sending_user)
            if isinstance(message, ParticipantLeaveVoiceChatMessage):
                self.remove_participant(participant)
            elif isinstance(message, ParticipantStartedCameraShareMessage):
                wx.CallAfter(wx.GetApp().program_frame.main_panel.current_voice_chat_panel.participant_viewer.enable_participant_camera, participant.username)
            elif isinstance(message, ParticipantStoppedCameraShareMessage):
                wx.CallAfter(wx.GetApp().program_frame.main_panel.current_voice_chat_panel.participant_viewer.disable_participant_camera, participant.username)
            elif isinstance(message, ParticipantStartedScreenShareMessage):
                wx.CallAfter(wx.GetApp().program_frame.main_panel.current_voice_chat_panel.participant_viewer.enable_participant_screen_share, participant.username)
            elif isinstance(message, ParticipantStoppedScreenShareMessage):
                wx.CallAfter(wx.GetApp().program_frame.main_panel.current_voice_chat_panel.participant_viewer.disable_participant_screen_share, participant.username)
        except ParticipantNotInCallException:
            pass

    def find_participant_through_username(self, username):
        """
        Gets a Participant object with the given username.
        :param username: str, the name of the participant.
        :return: Participant, the object of the participant.
        """
        for participant in self.participants:
            if participant.username == username:
                return participant
        raise ParticipantNotInCallException

    def handle_camera_data(self, participant):
        """
        Receives and handles camera data from a participant.
        :param participant: Participant, the participant that the function handles.
        """
        try:
            while participant.is_in_call:
                frame_bytes, address = self.communication_handler.receive_udp_message(participant.receive_camera_socket, CAMERA_DATA_BYTES)
                wx.CallAfter(wx.GetApp().program_frame.main_panel.current_voice_chat_panel.participant_viewer.set_participant_camera_image, participant.username, frame_bytes)
        except socket.error as e:
            print e
        finally:
            participant.receive_camera_socket.close()
            cv2.destroyAllWindows()

    def handle_screen_data(self, participant):
        """
        Receives and handles screen data from a participant.
        :param participant: Participant, the participant that the function handles.
        """
        try:
            while participant.is_in_call:
                screenshot_bytes, address = self.communication_handler.receive_udp_message(participant.receive_screen_socket, SCREEN_DATA_BYTES)
                wx.CallAfter(wx.GetApp().program_frame.main_panel.current_voice_chat_panel.participant_viewer.set_participant_screen_share_image, participant.username, screenshot_bytes)
        except socket.error as e:
            print e
        finally:
            participant.receive_screen_socket.close()

    def start_participant_threads(self, participant):
        """
        Starts the threads that listen and process the given participant's data.
        :param participant: Participant, the participant that the user should listen to.
        """
        #---- TO ALLOW CONNECTION BETWEEN DIFFERENT NETWORKS (ONLY 1 COMPUTER PER NETWORK) 
        #participant.receive_voice_socket.sendto("a", (participant.address[0], SERVER_PORT))
        #print "*** CONNECTED TO ADDRESS " + str((participant.address[0], SERVER_PORT))
        participant.receive_voice_thread = Thread(target=self.receive_voice_data, args=[participant])
        participant.process_voice_thread = Thread(target=self.process_voice_data, args=[participant])
        participant.camera_thread = Thread(target=self.handle_camera_data, args=[participant])
        participant.screen_thread = Thread(target=self.handle_screen_data, args=[participant])
        participant.voice_indication_thread = Thread(target=self.voice_indication_loop, args=[participant])
        participant.receive_voice_thread.start()
        participant.process_voice_thread.start()
        participant.camera_thread.start()
        participant.screen_thread.start()
        participant.voice_indication_thread.start()

    def stop_listening_to_all_participants(self):
        """
        Stops listening to all the participants by closing their sockets and then
        informing the server about newly opened ports.
        """
        new_open_ports = []
        for participant in self.participants:
            new_open_ports.extend(participant.get_used_ports_list())
            participant.is_in_call = False
            participant.close_sockets()
        self.using_client.communication_handler.send_new_open_ports_message(new_open_ports)

    def remove_participant(self, participant):
        """
        Completely removes a participant from the voice chat.
        if there are no more participants afterwards, closes the voice chat for good.
        :param participant: Participant, the participant the left the voice chat.
        """
        new_open_ports = participant.get_used_ports_list()
        participant.is_in_call = False
        participant.close_sockets()
        self.participants.remove(participant)
        print "DEBUG - REMOVED " + participant.username
        self.using_client.communication_handler.send_new_open_ports_message(new_open_ports)
        wx.CallAfter(wx.GetApp().set_voice_chat_participants_names, self.get_participant_names_list())
        wx.CallAfter(wx.GetApp().program_frame.main_panel.current_voice_chat_panel.participant_viewer.remove_participant_panel, participant.username)
        if not self.participants:  # there are no more participants, so voice chat is over and Chat Group is over too.
            self.using_client.close_voice_chat()
        self.using_client.update_called_user_information()

    def get_participant_names_list(self):
        """
        returns a list of the names of all participants in the voice chat.
        :return: [str], a list of the names of the participants.
        """
        return [participant.username for participant in self.participants]
