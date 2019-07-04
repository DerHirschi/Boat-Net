# just Linux - need pycryptodome
# Quelle : https://www.youtube.com/watch?v=G8UmQn9eofI&index=11&list=PLNmsVeXQZj7onbtIXvxZTzeKGnzI6NFp_
# The Morpheus Tutorials
# Edit: Masto

from Crypto import Random
from Crypto.Cipher import AES
import hashlib
import random
import string
from etc.log import log


def pad(strg):
    while len(strg) % 16 != 0:
        strg = strg + ' '
    return strg


def enc(_key, _msg):
    _iv = Random.new().read(16)
    _msg = pad(_msg).encode('UTF-8')
    _key = hashlib.sha256(str.encode(_key))
    _cipher = AES.new(_key.digest(), AES.MODE_CBC, _iv)
    return _cipher.encrypt(_msg), _iv


def dec(_key, _ci_txt, _iv):
    _key = hashlib.sha256(str.encode(_key))
    _cipher = AES.new(_key.digest(), AES.MODE_CBC, _iv)
    _temp = _cipher.decrypt(_ci_txt)
    try:
        return _temp.decode('UTF-8')
    except UnicodeError:
        log('Decrypt UnicodeError .. _temp: {}'.format(_temp), 1)
        log('Decrypt UnicodeError .. ci_txt: {}'.format(_ci_txt), 1)
        log('Decrypt UnicodeError .. iv: {}'.format(_iv), 1)
        return 0


def rand_key():
    _res = None
    for _ix in range(random.randint(3, 8)):
        _res = rand_string(40)

    return _res


def rand_string(n):
    return ''.join(random.choice(string.digits + string.ascii_letters) for _ in range(n))


if __name__ == "__main__":
    from etc.var import string2array, array2string

    ver = enc('test', 'test msg .. blas')
    print(type(ver))
    print(type(ver[0]))
    resfnc = ''
    resstr = ''

    for _a in range(len(ver)):

        temp = []
        tempstr = '%'

        for _i in range(len(ver[_a])):
            print(ver[_a][_i])
            temp.append(ver[_a][_i])
            tempstr = tempstr + str(ver[_a][_i]) + '%'

        resstr += tempstr
        print(temp)
        print(tempstr)

    print("--------------------------")
    resfnc = array2string(ver[0])
    print(resfnc)
    resfnc = array2string(ver[1])
    print(resfnc)
    ent = dec('test', ver[0], ver[1])
    print(ent)
