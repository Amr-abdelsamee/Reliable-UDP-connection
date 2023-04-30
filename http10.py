# HTTP 1.0 headers

import platform
from datetime import datetime


def get_http_request(
    method: str, file_name: str, data: str, host: str, user_agent: str
) -> str:
    """_summary: construct the header of the http request

    Args:
        method (str): GET/POST.
        file_name (str): requested file.
        host (str): the server.
        user_agent (str): the user agent of the client.

    Returns:
        message (str): the request of the http 1.0
    """
    message = f"{method} /{file_name} HTTP/1.0\nHost: {host}\nUser-Agent: {user_agent}"
    if method == "POST":
        message += f"Content-Type: text/html\nContent-Length: {len(data)}\n\n{data}"
    return message


def get_http_response(method, status_code, status, data, server):
    """_summary: construct the header of the http response

    Args:
        method (str): GET/POST
        status_code (str): 200/404
        status (str): OK/NOT FOUND
        data (str): used in case of GET to send the requested file not used in case of POST.
        server (str): the server.

    Returns:
        header (str): the response header of the http 1.0
    """
    system = platform.uname()
    now = datetime.now()

    header = (
        f"HTTP/1.0 {status_code} {status}\n"
        + f"Date: {now.strftime('%a, %d %b %Y %H:%M:%S %Z')}\n"
        + f"Server: {server} ({system[0]} {system[2]} {system[4]})\n"
        + f"Content-Length: {len(data)}\n"
        + "Content-Type: text/plain"
    )

    if method == "GET":
        header = header + f"\n\n{data}"
    return header
