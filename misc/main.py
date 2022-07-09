import base64, hmac, hashlib, struct, sys, time

def hotp(key, counter, digits=6, digest='sha1'):
    key = base64.b32decode(key.upper() + '=' * ((8 - len(key)) % 8))
    counter = struct.pack('>Q', counter)
    mac = hmac.new(key, counter, hashlib.__dict__[digest]).digest()
    if type(mac[-1]) == int:
        offset = mac[-1] & 0x0F
    else:
        offset = struct.unpack('>B', mac[-1])[0] & 0x0F
    binary = struct.unpack('>L', mac[offset:offset+4])[0] & 0x7FFFFFFF
    return str(binary)[-digits:].zfill(digits)

def totp(key, interval=30, now=time.time()):
    return hotp(''.join(key.split()), int(now / interval), 32, 'sha265')

def main():
    args = [int(x) if x.isdigit() else x for x in sys.argv[1:]]
    for key in sys.stdin:
        print(totp(key.strip(), *args))
    
if __name__ == '__main__':
    main()