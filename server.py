import asyncio
from loguru import logger
import network_requests 
import rksok_functions
import rksok_exceptions
import config

logger.add('debug.log', format = '{time} {level} {message}', rotation = '10 MB', compression = 'zip')

async def run_process(reader: asyncio.streams.StreamReader, writer: asyncio.streams.StreamWriter) -> None:
    '''main client session'''
    client_peername = writer.get_extra_info('peername')
    try:
        request_decoded = await asyncio.wait_for(network_requests.recieve_request(reader), timeout = 5)
    except asyncio.TimeoutError:
        response = rksok_functions.rksok_incorrect_request()
    else:
        try:
            validation_server_response = await network_requests.request_to_vragi_vezde(request_decoded, client_peername)
        except rksok_exceptions.ValidationServerNotResponded:
            result_of_check = rksok_functions.RESPONSE_STATUS['NOT_APPROVED']
        else:
            result_of_check = rksok_functions.is_approved(validation_server_response, client_peername)
        try:
            client_request = rksok_functions.Request(request_decoded)
            client_request.parse_request_decoded()
        except rksok_exceptions.IncorrectRKSOKRequest:
            logger.error('Error! Incorrect request')
            response = rksok_functions.rksok_incorrect_request()
        else:
            if result_of_check == rksok_functions.RESPONSE_STATUS['APPROVED']:
                response =  await rksok_functions.proccessing_response(client_request) 
            else:
                response = validation_server_response.encode()

    writer.write(response)
    await writer.drain()
    logger.info('Request processed successfully')
    logger.info(f'Response is {response.decode()}')
    logger.info(f"Close connection with client {client_peername}")
    writer.close()
    await writer.wait_closed() 

@logger.catch
async def main():
    server = await asyncio.start_server(
        run_process, config.RKSOK_SERVER['server'], config.RKSOK_SERVER['port'])
    addr = server.sockets[0].getsockname()
    logger.info(f'Serving on {addr}')

    async with server:
        await server.serve_forever()

asyncio.run(main())