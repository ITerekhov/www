import asyncio
from loguru import logger
import rksok_exceptions
import json
import aiofiles


REQUEST_VERB = {
    'GET': 'ОТДОВАЙ',
    'DELETE': 'УДОЛИ',
    'WRITE': 'ЗОПИШИ',
}
RESPONSE_STATUS = {
    'OK' : "НОРМАЛДЫКС",
    'NOT_FOUND' : "НИНАШОЛ",
    'APPROVED' : "МОЖНА",
    'NOT_APPROVED' : "НИЛЬЗЯ",
    'INCORRECT_REQUEST' : "НИПОНЯЛ"
}

PROTOCOL_VERSION = 'РКСОК/1.0'
VALIDATION_VERB = 'АМОЖНА?'

class Request:
    def __init__(self, request_decoded: str) -> None:
        self.request_decoded = request_decoded
        self.verb = None
        self.name = None
        self.phone = None
        self.protocol = None
    
    def parse_request_decoded(self) -> None:
        '''Function defines the attributes verb, name and phone'''
        self.list_data = self.request_decoded.split()
        self.verb = self.list_data[0]
        if self.verb not in REQUEST_VERB.values():
            raise rksok_exceptions.IncorrectRKSOKRequest
        elif self.verb == REQUEST_VERB['WRITE']:
            protocol = self.request_decoded.find(f'{PROTOCOL_VERSION}\r\n')
            if protocol == -1:
                raise rksok_exceptions.IncorrectRKSOKRequest
            else:
                self.protocol = PROTOCOL_VERSION
            self.phone = self.request_decoded[protocol+9:].strip()
            self.list_data = self.request_decoded[:protocol].split()
            self.verb = self.list_data.pop(0)
            self.name = ' '.join(self.list_data)
        else:
            self.verb = self.list_data.pop(0)
            protocol = self.list_data.pop(-1)
            if protocol != PROTOCOL_VERSION:
                raise rksok_exceptions.IncorrectRKSOKRequest
            else:
                self.protocol = PROTOCOL_VERSION
            self.name = ' '.join(self.list_data)
        if len(self.name) > 30 or self.verb not in REQUEST_VERB.values():
            raise rksok_exceptions.IncorrectRKSOKRequest

async def proccessing_response(client_request: Request) -> bytes:
    if client_request.verb == REQUEST_VERB['GET']:
        response = await get(client_request)
    elif client_request.verb == REQUEST_VERB['DELETE']:
        response = await delete(client_request)
    elif client_request.verb == REQUEST_VERB['WRITE']:
        response = await write(client_request)
    return response

def rksok_incorrect_request() -> bytes:
    '''return bytes-encoding message of incorrect rksok request'''
    response = f"{RESPONSE_STATUS['INCORRECT_REQUEST']} РКСОК/1.0\r\n\r\n".encode()
    return response

def rksok_validation_request(request_decoded: str) -> bytes:
    message = f'{VALIDATION_VERB} {PROTOCOL_VERSION}\r\n{request_decoded}\r\n\r\n'
    return message.encode()

def is_approved(validation_server_response: str, client_peername: str) -> str:
    '''Processes the validation server response'''
    if validation_server_response.split()[0] == RESPONSE_STATUS['NOT_APPROVED']:
        logger.info(f'Access denied!\r\nclient: {client_peername}\r\nrequest: {validation_server_response}')
        return RESPONSE_STATUS['NOT_APPROVED'] 
    else:
        logger.info(f'request processing allowed')
        return RESPONSE_STATUS['APPROVED']

async def get(request: Request) -> bytes:
    '''Function returns the requested data from the directory '''
    async with aiofiles.open('phonebook.txt', 'r', encoding='utf-8') as f:
        phonebook = await f.read()
    phonebook = json.loads(phonebook)
    if request.name in phonebook and phonebook[request.name] != None:
        phone = phonebook[request.name]      
        response = f"{RESPONSE_STATUS['OK']} РКСОК/1.0\r\n{phone}\r\n\r\n"
    else:
        response = f"{RESPONSE_STATUS['NOT_FOUND']} РКСОК/1.0\r\n\r\n"
    response = response.encode()
    return response


async def delete(request: Request) -> bytes:
    '''Function removes an entry from the directory '''
    async with aiofiles.open('phonebook.txt', 'r', encoding='utf-8') as f:
        phonebook = await f.read()
    phonebook = json.loads(phonebook)
    if request.name in phonebook and phonebook[request.name] != None:
        del phonebook[request.name]
        phonebook = json.dumps(phonebook)
        async with aiofiles.open('phonebook.txt', 'w', encoding='utf-8') as f:
            await f.write(phonebook)
        response = f"{RESPONSE_STATUS['OK']} РКСОК/1.0\r\n\r\n"
    else:
        response = f"{RESPONSE_STATUS['NOT_FOUND']} РКСОК/1.0\r\n\r\n"
    response = response.encode()
    return response


async def write(request: Request) -> bytes:
    '''Function enters data into the directory '''
    async with aiofiles.open('phonebook.txt', 'r', encoding='utf-8') as f:
        phonebook = await f.read()
    phonebook = json.loads(phonebook)
    phonebook[request.name] = request.phone
    phonebook = json.dumps(phonebook, ensure_ascii=False)
    async with aiofiles.open('phonebook.txt', 'w', encoding='utf-8') as f:
        await f.write(phonebook)
    response = f"{RESPONSE_STATUS['OK']} РКСОК/1.0\r\n\r\n".encode()
    return response   
