from Crypto.PublicKey import DSA
from Crypto.Signature import DSS
from Crypto.Hash import SHA256

# for hex conversion
import binascii

# to immediately call our a2_verify.py
import subprocess

# first get user input

print("\nWelcome to Sean's P2MS simulator. Please follow the instructions to execute the program.\n")

inM = input("Please enter the M-value, the number of signatures required for scriptSig : ")

inN = input("\nPlease enter the N-value, the number of public keys required for scriptPubkey : ")

N = int(inN)

M = int(inM)

# loop through N times to generate keys, then within each loop, generate 1 signature on the message, until M count reaches 0
# this way, the signatures are stored in the same order as the keys, which is important in the P2MS script

# open files to store keys and signatures

scriptPubKeyFile = open("scriptPubKey.txt", "wb")
scriptSigFile = open("scriptSig.txt", "wb")

delimeter = binascii.hexlify(bytes("!!!", 'utf-8'))

messageHash = SHA256.new(b"CSCI301 Contemporary Topics in Security 2023")

# inserting op code for M - number of signatures required in scriptPubKey.txt
opCodeM = binascii.hexlify(bytes("OP_" + inM, 'utf-8'))
scriptPubKeyFile.write(opCodeM)
scriptPubKeyFile.write(delimeter) # | chosen as delimeter


# inserting OP_0 for scriptSig

#2scriptSigFile.write(binascii.hexlify(bytes("OP_0", 'utf-8')))

for i in range (N):

    key = DSA.generate(1024)

    # get y, g, p, q params from key for signature
    tup = [key.y, key.g, key.p, key.q]

    # save hexed version of key.y to file

    pubKey = DSA.construct(tup)

    pubKeyHex = binascii.hexlify(pubKey.public_key().export_key())

    scriptPubKeyFile.write(pubKeyHex)

    scriptPubKeyFile.write(delimeter)

    # generate signature from message and save to file, if we can still create signatures
    
    if M > 0:
        
        #print("M is : " + str(M))
        M = M - 1

        signer = DSS.new(key, 'fips-186-3')
        signature = signer.sign(messageHash) 

        signature_hex = binascii.hexlify(signature)

        scriptSigFile.write(signature_hex)

        scriptSigFile.write(delimeter)

        #if M > 1:
        #    scriptSigFile.write(delimeter)

        '''

        verifier = DSS.new(pubKey, 'fips-186-3')

        try:
            verifier.verify(messageHash, signature)
            print("The message is authentic")

        except ValueError:
            print("The message is not authentic.")
        
        '''

opCodeN = binascii.hexlify(bytes("OP_" + inN, 'utf-8'))
scriptPubKeyFile.write(opCodeN)
scriptPubKeyFile.write(delimeter)

opCodeMulti = binascii.hexlify(bytes("OP_CHECKMULTISIG", 'utf-8'))
scriptPubKeyFile.write(opCodeMulti)

scriptPubKeyFile.close()
scriptSigFile.close()


print("\nProgram finished generating.")

print("\n" + inM + " Signatures generated from " + inN + " randomly generated Public Keys.")

print("\nExecuting Verify program.\n")
print("\n----------------------------------------------\n")

subprocess.run(["python3", "a2_verify.py"])


