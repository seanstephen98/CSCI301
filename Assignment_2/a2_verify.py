from Crypto.PublicKey import DSA
from Crypto.Signature import DSS
from Crypto.Hash import SHA256

# for hex conversion
import binascii

# for deep copying array
import copy

# function to read file and separate by delimeter

def readScriptPubFile (filename, delimeter):
    print("\nReading scriptPubKey File Now...\n")
    readFile = open(filename, "rb")
    hexedData = readFile.read()
    unhexedData = binascii.unhexlify(hexedData.strip().decode('utf-8'))
    unhexedData = str(unhexedData.decode('utf-8'))

    #print(unhexedData)
    returnArray = unhexedData.split(delimeter)
    #print(returnArray)
    readFile.close()
    return returnArray

def readScriptSigFile (filename, delimeter):
    print("\nReading scriptSig File Now...\n")
    readFile = open(filename, "rb")
    hexedData = readFile.read()
    unhexedData = binascii.unhexlify(hexedData.decode('utf-8'))

    #print(unhexedData)
    returnArray = unhexedData.split(delimeter)
    #print(returnArray)
    readFile.close()
    return returnArray


def isOpCode (OpCode):
    opDelimeter = "OP_"
    if opDelimeter not in OpCode:
        return False
    return True


def isMultiSig (OpCode):
    opDelimiter = "OP_"
    if not isOpCode(OpCode):
        return False
    code = OpCode.removeprefix(opDelimiter)
    if code == "CHECKMULTISIG":
        return True
    return False
    #print(code)

def isOpX (OpCode):
    opDelimiter = "OP_"
    if not isOpCode(OpCode):
        return False
    code = OpCode.removeprefix(opDelimiter)
    try:
        code = int(code)
        return True, code
    except:
        return False
    #print(code)

def checkScriptPubKeyFormatting (pubKeyArr):

    # check first element is multisig op code
    checkOpMulti = pubKeyArr.pop()
    if not isMultiSig(checkOpMulti):
        print("First element is not OP_CHECKMULTISIG.\n")
        improperFormatting()

    # check second element is N op code
    checkOpN = pubKeyArr.pop()
    expectedTrueandIntN = isOpX(checkOpN)

    # use N value to read N public keys
    for i in range (expectedTrueandIntN[1]):
        try:
            checkPubKey = DSA.import_key(pubKeyArr.pop())
        except:
            print("Public Keys cannot be generated. Check Formatting.\n")
            improperFormatting()
    
    # check that last value is OP_M 

    checkOPM = pubKeyArr.pop()
    expectedTrueandIntM = isOpX(checkOPM)

    # return M and N value to check scriptSig.txt
    return expectedTrueandIntM[1], expectedTrueandIntN[1]

# mainly to check the number of script sigs, and not more than N only
def checkScriptSigFormatting (scriptSigArr, M, N):
    # does the file really contain M signatures?

    #count = len(scriptSigArr) + 1 # account for OP_0
    count = len(scriptSigArr)
    if count != M:
        print("There number of signatures do not match OP_M.\n")
        improperFormatting()

    # does the file have more signatures than there are public keys?
    if count > N:
        print("There are more signatures than public keys.\n")
        improperFormatting()

    '''
    op0Delimiter = b"OP_0"
    if op0Delimiter not in scriptSigArr[1]:
        return False
    '''
    
    return True
    


def improperFormatting ():
    print("\nThere was a formatting error. Fix it and try the program again.")
    return

print("\nVerify program has begun. Reading scriptSig.txt and scriptPubKey.txt...\n")

delimeter = "!!!"


# reading scriptPubKey

pubKeyArr = readScriptPubFile("scriptPubKey.txt", delimeter)

# send a deep copy of the array to check the formatting

print("\nscriptPubKey File has been read. Checking Formatting Now...\n")
pubKeyArrCopy = copy.deepcopy(pubKeyArr)

MNarray = checkScriptPubKeyFormatting(pubKeyArrCopy)

print("\nFormatting of scriptPubKey File is correct.\n")

M = MNarray[0]
N = MNarray[1]

scriptSigArr = readScriptSigFile("scriptSig.txt", b"!!!")
print("\nscriptSig File has been read. Checking Formatting Now...\n")

#print(scriptSigArr)

# account for the last delimeter
scriptSigArr.pop()

scriptSigArrCopy = copy.deepcopy(scriptSigArr)

checkScriptSigFormatting(scriptSigArrCopy, M, N)

print("\nFormatting of scriptSig File is correct.\n")



# now all formatting is correct. we can push elements into the stack

print("\nCreating the stack now!\n")

P2MSScriptStack = []

# first, we hit the CHECKMULTISIG

checkMultiSig = pubKeyArr.pop()

if isMultiSig(checkMultiSig):
    print("\nHit OP_CHECKMULTISIG.\n")

    # then, all signatures go onto the stack
    # extend is used as it copies the elements item by item in order, instead of popping from the back

    print("\nPushing data from scriptSig File onto stack first.\n")

    P2MSScriptStack.extend(scriptSigArr)

    # then the scriptPubKey

    print("\nPushing data from scriptPubKey File onto the stack.\n")
    P2MSScriptStack.extend(pubKeyArr)

    #print(P2MSScriptStack)
    #print("\n\n\n")
    # now the stack is constructed. we simulate executing the CHECKMULTISIG script


    # we should first encounter OP_N
    OP_N = isOpX(P2MSScriptStack.pop())
    print("\nWe have hit OP_CODE N : OP_" + str(OP_N[1]) + "\n")
    # we use OP_N to pop off N public keys - into an array
    pubKeys = []

    print("\nPopping off " + str(OP_N[1]) + " Public Keys.\n")
    for i in range (OP_N[1]):
        #print(P2MSScriptStack)
        #print("\n\n\n")
        pubKeys.append(P2MSScriptStack.pop())

    # preserve the original order
    pubKeys.reverse()

    # we use OP_M to pop off M signatures - into an array

    OP_M = isOpX(P2MSScriptStack.pop())
    print("\nWe have hit OP_CODE M : OP_" + str(OP_M[1]) + "\n")
    sigs = []
    print("\nPopping off " + str(OP_N[1]) + " Signatures.\n")
    for i in range (OP_M[1]):
        #print(P2MSScriptStack)
        sigs.append(P2MSScriptStack.pop())

    # preserve the original order
    sigs.reverse()

    # now we compare each signature to each public key.

    matchCount = 0

    pubKeyIndex = 0

    messageHash = SHA256.new(b'CSCI301 Contemporary Topics in Security 2023')

    #print(sigs)
    #print("\n\n\n")
    #print(pubKeys)

    print("\nComparing each signature with each public key now. NOTE that the signatures MUST be in the same order as their matching public keys.\n")

    for sig in sigs:

        noMatch = True

        
        while noMatch:

            # here we simulate trying the signatures in order
            # the signatures MUST be in the same order as their corresponding public keys
            # hence the pubKey compared can only move on to the next one if the current signature matches
            # and if the current signature does not match the public key, then that public key is no longer compared
            verifier = DSS.new(DSA.import_key(pubKeys[pubKeyIndex]), 'fips-186-3')

            try:
                verifier.verify(messageHash, sig)
                matchCount = matchCount + 1
                pubKeyIndex = pubKeyIndex + 1
                #print("The message is authentic")
                noMatch = False
                break

            except ValueError:
                #print("The message is not authentic")
                noMatch = True

        '''
        # to check if any signatures match any public keys at all
        for key in pubKeys:


            verifier = DSS.new(DSA.import_key(key),'fips-186-3')

            try:
                verifier.verify(messageHash, sig)
                matchCount = matchCount + 1
                print("The message is authentic")
                break

            except ValueError:
                print("The message is not authentic")
                noMatch = True     
        '''  

    # after checking each signature with each public key in order
    # push 1 back into the stack if the number of matches are the same as M
    print("\nThere are " + str(matchCount) + " matching signatures.\n")
    if matchCount == OP_M[1]:
        P2MSScriptStack.append(1)

    try:
        expect1 = P2MSScriptStack.pop()
        if expect1 == 1:
            print("\nThe tally of valid signatures is equal to M. The signatures have unlocked the script!")

    except:
        print("\nThe signatures do not match the public keys. Try again.")

    









