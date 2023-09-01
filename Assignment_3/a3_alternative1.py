# hashlib for hash functions, json for formatting blocks
import json
import hashlib

# os to create directory, exit program
import os

# threading to allow both user's block creation functions to run concurrently
import threading

# time for sleep function to delay program, and to get the current time for creation of block
import time


# pubnub for real-time communication channel between the two users
from pubnub.callbacks import SubscribeCallback
from pubnub.enums import PNStatusCategory, PNOperationType
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

# standard pubnub functions and class
# only the function "message" provided by the standard pubnub code is modified
def my_publish_callback(envelope, status):
    # Check whether request successfully completed or not
    if not status.is_error():
        pass  # Message successfully published to specified channel.
    else:
        pass  # Handle message publish error. Check 'category' property to find out possible issue
        # because of which request did fail.
        # Request can be resent using: [status retry];

class MySubscribeCallback(SubscribeCallback):
    def presence(self, pubnub, presence):
        pass  # handle incoming presence data

    def status(self, pubnub, status):
        if status.category == PNStatusCategory.PNUnexpectedDisconnectCategory:
            pass  # This event happens when radio / connectivity is lost

        elif status.category == PNStatusCategory.PNConnectedCategory:
            pass
            # Connect event. You can do stuff like publish, and know you'll get it.
            # Or just use the connected event to confirm you are subscribed for
            # UI / internal notifications, etc
            #pubnub.publish().channel('Channel-Barcelona').message('Hello world!').pn_async(my_publish_callback)
        elif status.category == PNStatusCategory.PNReconnectedCategory:
            pass
            # Happens as part of our regular operation. This event happens when
            # radio / connectivity is lost, then regained.
        elif status.category == PNStatusCategory.PNDecryptionErrorCategory:
            pass
            # Handle message decryption error. Probably client configured to
            # encrypt messages and on live data feed it received plain text.

    def message(self, pubnub, message):
        # Handle new message stored in message.message
        #print(message.message, message.timetoken)

        #print(message.message, message.channel)

        # whenever the listener has received a block on its channel, send that block to the "static" class to store the blocks for that "round"
        listener_arbitrator_winner.addLatestPublishedBlocks(message.message)
    

# this class is used as a "static" class
# this class has functions to receive and store a block from each proposer in the block competition process
# then the list of proposed blocks can be judged to see which came first
# once the block is accepted as the next block on the chain, another function can clear the list of blocks to prepare for the next round of competition
class listener_arbitrator_winner:
    
    two_latest_blocks = []

    # called in MySubscribeCallback's message function 
    # whenever a block is sent in a pubnub channel, this method is called to save the proposed
    # block in this method's variable
    @classmethod
    def addLatestPublishedBlocks (cls, jsonBlock):
        #print("\nAddBlocks Called")
        listener_arbitrator_winner.two_latest_blocks.append(jsonBlock)

    # assume the blocks proposed in the current round has been submitted by the users
    # now we check the "Time" json field to find out which block was computed first
    # and declare which proposer created their block first

    # returns : winner block first, then loser block
    @classmethod
    def find_winner (cls):

        block0 = json.loads(listener_arbitrator_winner.two_latest_blocks[0])
        block1 = json.loads(listener_arbitrator_winner.two_latest_blocks[1])
        print("\nBlocks Proposed: ",  block0, block1)
        print("\n")
        #print(block0['Time'], block1['Time'])
        if block0['Time'] <= block1['Time']:
            
            print(block0['Proposer'] + " came first")
            return listener_arbitrator_winner.two_latest_blocks[0], listener_arbitrator_winner.two_latest_blocks[1]

        print(block1['Proposer'] + " came first")
        return listener_arbitrator_winner.two_latest_blocks[1], listener_arbitrator_winner.two_latest_blocks[0]
    
    # clear list of proposed blocks to prepare for next round
    @classmethod
    def clear_block_list (cls):
        listener_arbitrator_winner.two_latest_blocks.clear()




    
# class for 1x user (Bob or Alice) to accept transactions,
# then create blocks from the transactions (ideally threaded)
# broadcast message to only 1x other party's PubNub channel
class minr :
	
    def __init__(self, name, otherName, block0, seed) -> None:
        
        # save details for our object and 1x other object - the other party
        
        self.name = name
        self.otherName = otherName
        self.selfChannel = 'Channel-' + self.name
        self.otherChannel = 'Channel-' + self.otherName

        # seed is 0 or 1,000,000,000 to start the nonce, as specified by the brief
        self.seed = seed

        # each user creates a folder in their own name then saves the genesis block
        os.mkdir("./" + name)
        self.path = str ("./" + name + "/")
        self.saveBlock(block0, 0)


        # creating a pubnub object to add a listener on the user's channel,
        # pubnub object will be used to publish a proposed block too
        self.pnconfig = PNConfiguration()

        self.pnconfig.subscribe_key = 'sub-c-6b82e386-fb73-48b1-9450-4e50fcbbee22'
        self.pnconfig.publish_key = 'pub-c-78e5dd40-194d-4794-960c-507319affba1'
        self.pnconfig.user_id = name
        self.pubnub = PubNub(self.pnconfig)

        self.pubnub.add_listener(MySubscribeCallback())
        self.pubnub.subscribe().channels(self.selfChannel).execute()
	

    # accept 1 transaction, create a block based on that transaction
    # use a nonce starting from the specified "seed" value - 0  or 1,000,000,000
    def createBlock (self, count, transaction):

        # find the hash from the previous block
        previousBlockFile = open(self.path + str(count) + ".json", "rb")
        previousBlockHash = hashlib.sha256(previousBlockFile.read()).hexdigest()
        previousBlockFile.close()

        newCount = count + 1
        nonce = self.seed
        foundNonce = False

        # nonce is incremented by 1 at each iteration to find a hash of the 
        # resulting block that starts with with five zeroes 
        while not foundNonce:

            timenow = time.time()
            tx = json.dumps({'Block number': newCount, 'Hash': previousBlockHash, 'Transaction': transaction, 'Nonce' : nonce, 'Time' : timenow, 'Proposer': self.name}, sort_keys=True, indent=4, separators=(',', ': '))
            hashCheck = hashlib.sha256(tx.encode()).hexdigest()
            
            # 5 zeroes - publish block and end if found
            if int(hashCheck[0:8], 16) <= int("00000fff", 16) :
                print("\nSeed " + str(nonce) + " " + self.name + " block" + " Time proposed : " + str(timenow))
                self.publishBlock(tx)
                break

            nonce = nonce + 1

    # publish block in pubnub channel of other user

    def publishBlock (self, tx):

        self.pubnub.publish().channel(self.otherChannel).message(tx).pn_async(my_publish_callback)


    # save a block into a file

    def saveBlock (self, tx, count):

            try:
                newBlock = open(self.path + str(count) + ".json", "w+")
                newBlock.write(tx)
                newBlock.close()
            except:
                print("Error saving block")

    # verify block

    def verifyBlock (self, block, count):

        try:
            # find the hash from the previous block
            previousBlockFile = open(self.path + str(count - 1) + ".json", "rb")
            previousBlockHash = hashlib.sha256(previousBlockFile.read()).hexdigest()
            previousBlockFile.close()

            blockjson = json.loads(block)

            if blockjson["Hash"] == previousBlockHash:
                print("\n" + self.name + ": Block is verified.")
                return True
            else:
                print("\n" + self.name + ": Block is not verifiable! Discarded.")
                return False

        except:
            print("Error verifying block")


    # stop pubnub functions
    def teardown (self):
        self.pubnub.unsubscribe_all()
        self.pubnub.stop()
        


	
# initialiser list of transactions

transactions = [ "[3, 4, 5, 6]", "[4, 5, 6, 7]", "[5, 6, 7, 8]", "[6, 7, 8, 9]", "[7, 20, 9, 10]", "[8, 9, 10, 11]", "[9, 10, 11, 12]", "[10, 11, 12, 13]", "[11, 12, 13, 14]", "[12, 13, 14, 15]", "[13, 14, 15, 16]"]

# genesis block

block0 = json.dumps({'Block number': 0, 'Hash': "Genesis", 'Transaction': "", "Nonce" : 0, "Time" : time.time()}, sort_keys=True, indent=4, separators=(',', ': '))


# creating users

name1 = "Alice"
name2 = "Bob"

person1 = minr(name1, name2, block0, 0)
person2 = minr(name2, name1, block0, 1000000000)

count = 0

"""
    how the loop works::
    for each transaction in transactions, each user will look for an appropriate nonce and create a proposed block if found

        this is broadcasted to the other user's pubnub channels and each user's pubnub listener will send the received block to a handler listener_arbitrator_winner class

        the threads are then joined and then the handler class will compare the two received blocks and determine which block came first

        this does not ensure that the block is "verified" in accordance to lab 4 task 8's method of checking the hash of the previous block against the hash included in the current block

        as spoken with the tutor, the "winning" block will still need to be verified by each user

        if the winning block can be verified, it will be saved by both users

        if the winning block can not be verified, the losing block will be verified

        if the losing block can not be verified, the two users compete to find a valid block again

"""

for transaction in transactions:

    print("\n***************Round " + str(count) + "***************")

    blockVerified = False

    while not blockVerified:

        # create threads to let the two functions run concurrently

        thread1 = threading.Thread(target=person1.createBlock, args=(count, transaction))
        thread2 = threading.Thread(target=person2.createBlock, args=(count, transaction))

        # start threads execution

        thread1.start()
        thread2.start()

        # end threads execution
        # Note that it has been tested that even after calling the join() method, the threads occasionally continue running
        # using time.sleep seems to be an accepted method to address this. initialising time.sleep with 5 seconds is the most consistent so far with no issues
        # lower sleep times have allowed threads to continue running still

        thread1.join()
        thread2.join()

        time.sleep(5)

        winningBlock, losingBlock = listener_arbitrator_winner.find_winner()

        count = count + 1
        
        person1Verify = person1.verifyBlock(winningBlock, count)
        person2Verify = person2.verifyBlock(winningBlock, count)

        if (person1Verify == True and person2Verify == True):

            print("\nFirst Proposed Block Verified and Saving...")

            person1.saveBlock(winningBlock, count)
            person2.saveBlock(winningBlock, count)

            listener_arbitrator_winner.clear_block_list()
            blockVerified == True
            break
        else:

            print("\nBlock not verified by both parties. Checking other block...")

            person1Verify = person1.verifyBlock(losingBlock, count)
            person2Verify = person2.verifyBlock(losingBlock, count)

            if (person1Verify == True and person2Verify == True):

                print("\Second Proposed Block Verified and Saving...")

                person1.saveBlock(losingBlock, count)
                person2.saveBlock(losingBlock, count)

                listener_arbitrator_winner.clear_block_list()
                blockVerified == True
                break
            else:
                print("\nBlock not verified by both parties. Both parties recreating new blocks...")


print("\nAll transactions have been added to the blockchain. Goodbye.")

os._exit(0)