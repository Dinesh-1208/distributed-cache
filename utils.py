import logging
import json

def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)
    logger.propagate = False
    return logger

def send_message(sock, msg_dict):
    msg_str = json.dumps(msg_dict)
    sock.sendall((msg_str + '\n').encode('utf-8'))

def receive_message(sock):
    data = b""
    while b"\n" not in data:
        chunk = sock.recv(1024)
        if not chunk:
            break
        data += chunk
    if not data:
        return None
    try:
        return json.loads(data.decode('utf-8').strip())
    except Exception:
        return None
