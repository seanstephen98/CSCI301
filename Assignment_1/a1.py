import glob # for file reading

import os # for creating directory

# for symmetric encryption

from base64 import b64encode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes

from base64 import b64decode
from Crypto.Util.Padding import unpad

# for public key encryption

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP


# create directory to store all outputs of the encryption

path = "./encryption_output"

if not os.path.exists(path):
    os.mkdir(path)
else:
    print("Output folder cannot be created. Try again.")
    exit


# def function for finding all text files and reading into a file

def findAndListFiles ():

    try:
        Fileout = open("./encryption_output/names.namelist", "xt")
        for item in glob.glob("*.txt"):
            Fileout.write(item + "\n")

        Fileout.close()        
    except:
        print("Namelist could not be created or already exists. Try again.")

# function to read from the list of files

def readNameList ():
    listOfNames = []
    try:
        with open("./encryption_output/names.namelist") as Filein:
            while line := Filein.readline():
                listOfNames.append(line.strip())
        #print(listOfNames) 
        Filein.close()
    except:
        print("Namelist does not exist. Try again.")  
    return listOfNames


# encrypting all text files

def encryptAllFiles ():

    listOfNames = readNameList()

    # generate cipher

    # create key
    key = get_random_bytes(16)

    # AES CBC cipher object
    cipher = AES.new(key, AES.MODE_CBC)

    # generate iv
    iv = b64encode(cipher.iv).decode('utf-8')

    # reformat key
    key = b64encode(key).decode('utf-8')

    # create files with iv and key, to be encrypted with Public Key Encryption
    try:
        ivFile = open("./encryption_output/ivfile.iv", "xt")
        ivFile.write(iv)
        ivFile.close()

        symKeyFile = open("./encryption_output/symkey.key", "xt")
        symKeyFile.write(key)
        symKeyFile.close()

    except:
        print("Error. Try again.")
        exit


    
    # loop through all files, then create an encrypted version for each file

    for filename in listOfNames:

        #  open and read file
        with open(filename) as Filein:
            plaintext = Filein.read()
            #while line := Filein.readline():
            #    plaintext += line
        Filein.close()
        #print(plaintext)
        
        # create encrypted version
        outFile = open("./encryption_output/" + filename + ".enc", "xt")
        plaintext = str.encode(plaintext) # we need to convert the string to byte_string
        ct_bytes = cipher.encrypt(pad(plaintext, AES.block_size))
        ct = b64encode(ct_bytes).decode('utf-8')
        outFile.write(ct)
        outFile.close()

# function to generate a pair of public and private keys

def generateRSAKeys (name):

    key = RSA.generate(2048)
    private_key = key.export_key()
    file_out = open("./encryption_output/" + name + "_private.pem", "wb")
    file_out.write(private_key)
    file_out.close()

    public_key = key.publickey().export_key()
    file_out = open("./encryption_output/" + name + "_public.pem", "wb")
    file_out.write(public_key)
    file_out.close()


# function to encrypt symkey file

def encryptSymKey ():

    receiver_public_key = RSA.import_key(open("./encryption_output/receiver_public.pem").read())
    symkey = open("./encryption_output/symkey.key" ,"rb").read()
    Fileout = open("./encryption_output/symkey_encrypted.key", "wb")
    cipher_rsa = PKCS1_OAEP.new(receiver_public_key)
    enc_data = cipher_rsa.encrypt(symkey)
    Fileout.write(enc_data)
    Fileout.close()



# function to decrypt symkey file

def decryptSymKey ():

    Filein = open("./encryption_output/symkey_encrypted.key", "rb")
    private_key = RSA.import_key(open("./encryption_output/receiver_private.pem").read())
    enc_data = Filein.read(private_key.size_in_bytes())
    cipher_rsa = PKCS1_OAEP.new(private_key)
    plaintext = cipher_rsa.decrypt(enc_data)
    Filein.close()
    return plaintext


# decrypting the text files

def decryptAllFiles ():
    
    listOfNames = readNameList()
    iv = ""
    symKey = ""
    # read files with iv and key, create cipher again
    try:

        ivFile = open("./encryption_output/ivfile.iv", "r")
        iv = ivFile.read()
        iv = b64decode(iv)
        ivFile.close()

        print("Using receiver's private key to decrypt the symmetric key.\n")
        symKey = decryptSymKey()
        print("Done decrypting the encrypted symmetric key.\n")
        symKey = b64decode(symKey)

    except:
        print("Error. Try again.")
        exit

    decipher = AES.new(symKey, AES.MODE_CBC, iv)
    # loop through all files, then create a decrypted version for each file

    for filename in listOfNames:

        #  open and read file
        with open("./encryption_output/" + filename + ".enc") as Filein:
            readText = Filein.read()
        Filein.close()
        #print(plaintext)
        
        # create encrypted version
        try:

            outFile = open("./encryption_output/" + filename, "xt")
            readText = b64decode(readText)
            plaintext = unpad(decipher.decrypt(readText), AES.block_size)
            plaintext = plaintext.decode('utf-8')
            outFile.write(plaintext)
            outFile.close()

        except ValueError:
            print("Incorrect Decryption")
        except KeyError:
            print("Incorrect Key")



# calling functions, printing current location while running
 
print("Finding all .txt files in the directory...\n")

findAndListFiles()

print("Found target files. Created a list of all files. Encrypting with symmetric encryption now.\n")

encryptAllFiles()

print("Generating key pairs for sender and receiver...\n")

generateRSAKeys("sender")

generateRSAKeys("receiver")

print("Key pairs generated. Encrypting .key file.\n")

encryptSymKey()

print("Symmetric key file has been encrypted with receiver's public key. Let's decrypt our files now.\n")

decryptAllFiles()

print("All done! Demonstration of hybrid encryption is complete!\n")







        