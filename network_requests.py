import asyncio
from loguru import logger
import config
import rksok_functions
import rksok_exceptions


async def recieve_request(reader: asyncio.streams.StreamReader) -> str:
    '''Function accepts request from a client. Return request data '''
    logger.info('receiving request...')
    raw_data = b''
    while True:
        data = await reader.read(1024)
        raw_data += data
        if not data or data.endswith(b'\r\n\r\n'):
            break
    request_decoded = raw_data.decode()
    return request_decoded


async def request_to_vragi_vezde(request_decoded: str, client_peername: tuple) -> str:
    '''Function ask the validation server for permission to process the request. Return the server's response'''
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(
            config.VALIDATION_SERVER['server'], config.VALIDATION_SERVER['port']), timeout = 20)
    except asyncio.TimeoutError:
            logger.error('The validation server is not responding')
            raise rksok_exceptions.ValidationServerNotResponded
    else:
        message = rksok_functions.rksok_validation_request(request_decoded) 
        logger.info(f'Send request from {client_peername} to validation server')
        writer.write(message)
        await writer.drain()
        response = b''
        while True:
            data = await reader.read(1024)
            response += data
            if not data or data.endswith(b'\r\n\r\n'):
                break
        response = response.decode()
        logger.info('Close connection with validation server')
        writer.close()
        return response
