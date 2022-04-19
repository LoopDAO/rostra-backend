import hashlib

import rsa

import ckb.segwit_addr as sa


def ckbhash():
    return hashlib.blake2b(digest_size=32, person=b'ckb-default-hash')
# ref: https://github.com/nervosnetwork/rfcs/blob/master/rfcs/0021-ckb-address-format/0021-ckb-address-format.md
FORMAT_TYPE_FULL      = 0x00
FORMAT_TYPE_SHORT     = 0x01
FORMAT_TYPE_FULL_DATA = 0x02
FORMAT_TYPE_FULL_TYPE = 0x04

CODE_INDEX_SECP256K1_SINGLE = 0x00
CODE_INDEX_SECP256K1_MULTI  = 0x01
CODE_INDEX_ACP              = 0x02

BECH32_CONST = 1
BECH32M_CONST = 0x2bc830a3

def generateShortAddress(code_index, args, network = "mainnet"):
    """ generate a short ckb address """
    hrp = {"mainnet": "ckb", "testnet": "ckt"}[network]
    hrpexp =  sa.bech32_hrp_expand(hrp)
    format_type  = FORMAT_TYPE_SHORT
    payload = bytes([format_type, code_index]) + bytes.fromhex(args)
    data_part = sa.convertbits(payload, 8, 5)
    values = hrpexp + data_part
    polymod = sa.bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ BECH32_CONST
    checksum = [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]
    combined = data_part + checksum
    addr = hrp + '1' + ''.join([sa.CHARSET[d] for d in combined])
    return addr

def generateFullAddress(code_hash, hash_type, args, network = "mainnet"):
    hrp = {"mainnet": "ckb", "testnet": "ckt"}[network]
    hrpexp =  sa.bech32_hrp_expand(hrp)
    format_type  = FORMAT_TYPE_FULL
    payload = bytes([format_type]) + bytes.fromhex(code_hash)
    payload += bytes([hash_type]) + bytes.fromhex(args)
    data_part = sa.convertbits(payload, 8, 5)
    values = hrpexp + data_part
    polymod = sa.bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ BECH32M_CONST
    checksum = [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]
    combined = data_part + checksum
    addr = hrp + '1' + ''.join([sa.CHARSET[d] for d in combined])
    return addr

def get_ckb_address_from_pubkey(pubkey):
    mainnet = "mainnet"
    testnet = "testnet"
    sign_script = bytes.fromhex(pubkey)
    hasher = ckbhash()
    hasher.update(sign_script)
    sign_script_hash = hasher.hexdigest()
    args = sign_script_hash[:40]
    print("code_hash to encode:\t", sign_script_hash)
    
    print("==========================================================")
    print("sign script:\t", sign_script.hex())
    print("args to encode:\t\t", args)
    mainnet_addr_short = generateShortAddress(0x00, args, mainnet)
    testnet_addr_short = generateShortAddress(0x02, args, testnet)
    #testnet_addr_full = generateFullAddress(code_hash, hash_type, args, testnet)
    
    code_hash = '577a5e5930e2ecdd6200765f3442e6119dc99e87df474f22f13cab819c80b242'
    #args = '1af305ff5790e2ac7c6f33d3dbf4f28e2afdb849'
    testnet_addr_full = generateFullAddress(code_hash, 0x01, args, testnet)
    return testnet_addr_full
    

