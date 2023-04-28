# HTTP 1.0 headers

import platform
from datetime import datetime

def http_request(method, file_name, host="localhost", browser="browserX/2.0", data=""):
    """_summary: construct the header of the http request

    Args:
        method (str): GET/POST.
        file_name (str): requested file.
        host (str, optional): the server. Defaults to "localhost".
        browser (str, optional): the browser of the client. Defaults to "browserX/2.0".

    Returns:
        header (str): the request header of the http 1.0
    """

    system = platform.uname()
    User_Agent = browser + ' (' + system[0] +' '+ system[2] +' '+ system[4] + ')'

    header = (
    method + " /" + file_name + " HTTP/1.0" + "\n" +
    "User_Agent: " + User_Agent  + "\n" +
    "Host: " + host + "\n" 
    )

    if method == "POST":
        header_p1 = (
        "Content-Type: text/plain" + "\n"
        "Content-Length: " + str(len(data)) 
        )
        header =  header + header_p1 + "\n\n" + data
    return header

# most common types of Content-Type:
# text/html
# text/plain
# application/json
# application/xml
# image/jpeg
# image/png

def http_response(method, status_code, status,  data="", browser="browserX/2.0"):
    """_summary: construct the header of the http response

    Args:
        method (str):  GET/POST
        status_code (str): 200/404
        status (str): OK/NOT FOUND
        data (str, optional): used in case of GET to  send the requested file not used in case of POST. Defaults to "".
        browser (str, optional): the browser of the server. Defaults to "browserX/2.0".

    Returns:
        header (str): the responde header of the http 1.0
    """
    system = platform.uname()
    now = datetime.now()

    header = (
    "HTTP/1.0 " + status_code + " " + status + "\n" +
    "Date: " + now.strftime("%a, %d %b %Y %H:%M:%S %Z") + "\n" +
    "Server: " + browser + ' (' + system[0] +' '+ system[2] +' '+ system[4] + ')\n' +
    "Content-Length: " + str(len(data)) + "\n" +
    "Content-Type: " + "text/plain"
    )
    
    if method == "GET":
        header = header + "\n\n" + data
    return header


# example:
# HTTP/1.0 200 OK
# Date: Fri, 26 Apr 2023 20:13:47 GMT
# Server: Apache/2.2.22 (Ubuntu)
# Last-Modified: Tue, 30 Oct 2022 16:13:47 GMT
# ETag: "a0f-4d8-4e9f9f9f9f9f9"
# Accept-Ranges: bytes
# Content-Length: 1234
# Connection: close
# Content-Type: text/html