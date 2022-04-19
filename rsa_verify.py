

import logging

import rsa

from ckb.ckb_address import get_ckb_address_from_pubkey


def flashsigner_verify(message, signature,user_addr, hash_method="SHA-256"):
    try:
        pubkey = signature[:520]
        
        address = get_ckb_address_from_pubkey(pubkey)
        print("address:\t", address)
        if(address != user_addr):
            logging.error("address not match")
            return False
        
        pubkey = bytearray.fromhex(pubkey)
        e = pubkey[0:4]
        n = pubkey[4:]
        pub = rsa.PublicKey(int.from_bytes(n, "little"),
                            int.from_bytes(e, "little"))
        signature_ = bytearray.fromhex(signature[520:])
        compare_hash_method = hash_method

        hash_m = rsa.verify(message.encode(), signature_, pub)
        if hash_m == compare_hash_method:
            return True
        else:
            return False
    except OSError as err:
        logging("OS error: {0}".format(err))
    except ValueError:
        logging("Could not convert data to an integer.")
    except BaseException as err:
        logging(f"Unexpected %s, %s", (err, type(err)))
    return False
