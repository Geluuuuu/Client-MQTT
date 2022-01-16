messageTypes = {
    'CONNECT': b'\x10',
    'CONNACK': b'\x20',
    'PUBLISH': 3,
    'PUBACK': b'\x40',
    'PUBREC': b'\x50',
    'PUBREL': b'\x62',
    'PUBCOMP': b'\x70',
    'SUBSCRIBE': 8,
    'SUBACK': b'\x90',
    'UNSUBSCRIBE': 10,
    'UNSUBACK': b'\xB0',
    'PINGREQ': b'\xC0',
    'PINGRESP': b'\xD0',
    'DISCONNECT': b'\xE0',
}

class Connect(object):
    def __init__(self, _id, _username, _password, _keepAlive, _cleanSession, _lastWillTopic, _lastWillMessage, _lastWillQos, _lastWillRetain):
        self.__id = _id
        self.__username = _username
        self.__password = _password
        self.__keepAlive= _keepAlive
        self.__cleanSession = _cleanSession
        self.__lastWillTopic= _lastWillTopic
        self.__lastWillMessage = _lastWillMessage
        self.__lastWillQos= _lastWillQos
        self.__lastWillRetain = _lastWillRetain

        self.willFlag = None
        if (_lastWillMessage != None):
            self.willFlag = 1

        if (_lastWillQos != None):
            Qo2B0 = (self.__lastWillQos & 1)
            if (Qo2B0 == 0):
                Qo2B0 = None

            Qo2B1 = ((self.__lastWillQos >> 1) & 1)
            if (Qo2B1 == 0):
                Qo2B1 = None
        else:
            Qo2B0 = None
            Qo2B1 = None

        #facem o lista cu valorile ce ar putea aparea in payload, ne ajuta la determinarea flagului
        self.mapConnParam = [_username, _password, _lastWillRetain, Qo2B1, Qo2B0, self.willFlag, _cleanSession, None]

    #scoatem valoarea flagului care indica ce valori avem in payload
    def getFlagValue(self):
        putere = 7
        flagValue = 0
        for value in self.mapConnParam:
            if value != None:
                flagValue = flagValue + 2 ** putere
            putere = putere - 1

        return (flagValue).to_bytes(1, byteorder='big')

    def makePacket (self):
        #Variable header
        variableHeader = b'\x00\x04' #length mqtt string
        variableHeader += ('MQTT').encode ('UTF-8') #protocol name
        variableHeader += b'\x04' #version of mqtt
        variableHeader += self.getFlagValue() #flag
        variableHeader += (self.__keepAlive).to_bytes (2, byteorder='big') #keep alive

        #payload
        #set Id
        payload = (len (str(self.__id))).to_bytes (2, byteorder='big')
        payload += str(self.__id).encode ('UTF-8')

        if (self.willFlag != None):
            payload += (len (self.__lastWillTopic)).to_bytes (2, byteorder='big')
            payload += self.__lastWillTopic.encode ('UTF-8')

            payload += (len (self.__lastWillMessage)).to_bytes (2, byteorder='big')
            payload += self.__lastWillMessage.encode ('UTF-8')

        if (self.__username != None):
            payload += (len (self.__username)).to_bytes (2, byteorder='big')
            payload += self.__username.encode ('UTF-8')


        if (self.__password):
            payload += (len (self.__password)).to_bytes (2, byteorder='big')
            payload += self.__password.encode ('UTF-8')

        stringConcat = variableHeader + payload

        finalPacket = messageTypes['CONNECT']
        finalPacket += len(stringConcat).to_bytes(1, byteorder='big')
        finalPacket += stringConcat
        return finalPacket

class Disconnect (object):
    def makePacket (self):
        packet = bytearray ()
        packet += messageTypes['DISCONNECT']

        packet += b'\x00'

        return packet

class PingReq (object):
    def makePacket (self):
        packet = bytearray ()
        packet += messageTypes['PINGREQ']

        packet += b'\x00'

        return packet

class Pingresp (object):
    def parseData (self, packet):
        return 'Pingresp'

class Publish (object):
    def __init__ (self, _topicName, _message, _Qos, _dup, _retain, packetIdentifier):
        self.__topicName = _topicName
        self.__message = _message
        self.__Qos = _Qos
        self.__dup = _dup
        self.__retain = _retain
        self.__packetIdentifier = packetIdentifier

        self.Qo2B0 = (self.__Qos & 1)

        self.Qo2B1 = ((self.__Qos >> 1) & 1)

    def makePacket (self):
        valFixedHeader = messageTypes['PUBLISH'] * 16 + (self.__dup * 8) + (self.Qo2B1 * 4) + (self.Qo2B0 * 2) + (self.__retain * 1)
        finalPacket = valFixedHeader.to_bytes(1, byteorder='big')

        #make variable header
        variableHeader = (len (self.__topicName)).to_bytes(2, byteorder='big')
        variableHeader += (self.__topicName).encode('UTF-8')

        if self.__Qos == 1 or self.__Qos == 2:
            variableHeader += (self.__packetIdentifier).to_bytes(2, byteorder='big')

        payload = (len(self.__message)).to_bytes(2, byteorder='big')
        payload += (self.__message).encode ('UTF-8')

        stringConcat = variableHeader + payload
        remainingLength = (len(stringConcat)).to_bytes(1, byteorder='big')

        finalPacket += remainingLength + stringConcat

        return finalPacket

class Subscribe (object):
    def __init__ (self, _topicList, _QosList, _pachetIdentifier):
        self.__topicList = _topicList
        self.__QosList = _QosList
        self.__pachetIdentifier = _pachetIdentifier

    def makePacket (self):
        valFixedHeader = messageTypes['SUBSCRIBE'] * 16 + 2
        finalPacket = valFixedHeader.to_bytes(1, byteorder='big')

        variableHeader = self.__pachetIdentifier.to_bytes(2, byteorder='big')

        n = len (self.__topicList)
        payload = bytearray ()
        for i in range (0, n):
            payload += (len(self.__topicList[i])).to_bytes(2, byteorder='big')
            payload += (self.__topicList[i]).encode ('UTF-8')

            payload += (self.__QosList[i]).to_bytes(1, byteorder='big')

        stringConcat = variableHeader + payload
        remainingLength = (len(stringConcat)).to_bytes(1, byteorder='big')

        finalPacket += remainingLength + stringConcat

        print (finalPacket)
        return finalPacket

class Subpack (object):
    def parseData (self, packet):
        responseHigh = packet[2]
        responseLow = packet[3]

        response = (responseHigh << 2) + responseLow

        return response

class Unsubscribe (object):
    def __init__ (self, _topicList, _packetIdentifier):
        self.__topicList = _topicList
        self.__packetIdentifier = _packetIdentifier

    def makePacket (self):
        valFixedHeader = messageTypes['UNSUBSCRIBE'] * 16 + 2
        finalPacket = valFixedHeader.to_bytes(1, byteorder='big')

        variableHeader = self.__packetIdentifier.to_bytes(2, byteorder='big')

        n = len (self.__topicList)
        payload = bytearray ()
        for i in range (0, n):
            payload += (len(self.__topicList[i])).to_bytes(2, byteorder='big')
            payload += (self.__topicList[i]).encode ('UTF-8')

        stringConcat = variableHeader + payload
        remainingLength = (len(stringConcat)).to_bytes(1, byteorder='big')

        finalPacket += remainingLength + stringConcat

        return finalPacket

class Unsuback (object):
    def parseData (self, packet):
        responseHigh = packet[2]
        responseLow = packet[3]

        response = (responseHigh << 2) + responseLow

        return response

class Pubrel (object):
    def makePacket (self, _pachetIdentifier):
        packet = bytearray ()
        packet += messageTypes['PUBREL']

        packet += b'\x02'
        packet += _pachetIdentifier.to_bytes(2, byteorder='big')

        return packet

class Pubrec (object):
    def parseData (self, packet):
        responseHigh = packet[2]
        responseLow = packet[3]

        response = (responseHigh << 2) + responseLow

        return response

class Connack (object):
    def parseData (self, packet):
        response = packet[3]
        if response == 0:
            return 'Connection accepted'
        if response == 1:
            return 'Connection Refused, unacceptable protocol version'
        if response == 2:
            return 'Connection Refused, identifier rejected'
        if response == 3:
            return 'Connection Refused, Server unavailable'
        if response == 4:
            return 'Connection Refused, bad user name or password'
        if response == 5:
            return 'Connection Refused, not authorized'

        return 'Unknown error'

class Puback (object):
    def parseData (self, packet):
        responseHigh = packet[2]
        responseLow = packet[3]

        response = (responseHigh << 2) + responseLow

        return response

class Pubcomp (object):
    def parseData (self, packet):
        responseHigh = packet[2]
        responseLow = packet[3]

        response = (responseHigh << 2) + responseLow

        return response