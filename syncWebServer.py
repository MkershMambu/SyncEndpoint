import sys
import aiohttp
import asyncio
import json
import uuid
from vibora import Vibora, JsonResponse, Request, Response
from multiprocessing import Manager

app = Vibora()

# dictionary of asyncio.Event() key'ed by unique responseID
responseEvents = {}
responseDetails = {
    "ID121324242": "This is the response back"
}

# Config will be a new component.
class Config:
    def __init__(self):
        self.name = 'Vibora Component'
        self.responseEvents = {}
        self.responseDetails = {}
    def addEvent(self,responseID):
        self.responseEvents[responseID] = asyncio.Event()
    def getEvent(self,responseID):
        return self.responseEvents[responseID]
    def setEvent(self,responseID):
        self.responseEvents[responseID].set()
    def addResponse(self,responseID, responseStr):
        self.responseDetails[responseID] = responseStr
    def getResponse(self,responseID):
        return self.responseDetails[responseID]
    def clearAll(self,responseID):
        del self.responseEvents[responseID]
        del self.responseDetails[responseID]
    def setName(self,nm):
        self.name = nm
    def getName(self):
        return self.name



# Registering the config instance.
confg = Config()
confg.setName("Set Name as part of startup")
confg.addEvent("MKTEST1")
app.components.add(confg)

def getUniqueResponseID():
    return str(uuid.uuid4())

serverURLPath = "http://127.0.0.1:80"

@app.route('/', methods=['GET', 'POST'])
async def home(request : Request, config: Config):
    printx("[1a] / called")
    responseID = getUniqueResponseID()
    config.addEvent(responseID)
    # responseEvents[responseID] = asyncio.Event()
    if request.method != b'POST':
        return JsonResponse({'ERROR': 'Need to call using POST'})
    requestBody = await request.json()
    try:
        methodToCall = requestBody['methodToCall']
        params = requestBody['params']
    except:
        return JsonResponse({'ERROR': 'Wrong parameters posted. Expect methodToCall and params'})

    params['callbackResponseID'] = responseID
    params['callbackURL'] = f"{serverURLPath}/response"
    printx(f"[1b] / calling {methodToCall}")
    async with aiohttp.ClientSession() as session:
        async with session.post(methodToCall,
            data=json.dumps(params)) as r:
                responseStr = await r.text()
                printx("[1c] MPO startup call returned:")

    printx('[1d] In webserver waiting for response ...')
    printx(config.responseEvents)
    await config.getEvent(responseID).wait()
    # await responseEvents[responseID].wait()
    printx('[1e] received response ...')
    responseObj = config.getResponse(responseID)
    config.clearAll(responseID)
    return JsonResponse(responseObj)

@app.route('/response', methods=['POST'])
async def responseReceiver(request : Request, config: Config):
    # Really strange but the next call to dummy (or a print statement) is needed here for this method to work consistently??
    dummy()
    printx("[4] In /response")
    requestBody = await request.json()
    responseID = requestBody['callbackResponseID']
    # current_config = request.components.get(Config)
    configName = config.getName()
    
    printx(f"[4a] responding for {responseID} - Config Name: |{configName}|")
    printx(config.responseEvents)
    config.addResponse(responseID,requestBody)
    config.setEvent(responseID)
    return JsonResponse({'msg': 'ok'})

@app.route('/dummyMPOEndpoint', methods=['POST'])
async def mpoTest(request : Request):
    printx("[2] dummyMPOEndpoint called")
    requestBody = await request.json()
    loop = asyncio.get_event_loop()
    loop.create_task(mpoEndpointTask(requestBody))
    return JsonResponse({'success': 'OK'})

@app.route('/TestEndpoint', methods=['GET'])
async def mpoTest(request : Request):
    printx("[5] TestEndpoint called")
    return JsonResponse({'success': 'OK'})

async def mpoEndpointTask(params):
    printx("[3] mpoEndpointTask called")
    callbackResponseID = params['callbackResponseID'] 
    callbackURL = params['callbackURL']
    returnParams = {'callbackResponseID': callbackResponseID, 'msg': 'Response from the MPO process called'}
    printx("[3a] calling {callbackURL}")
    async with aiohttp.ClientSession() as session:
        async with session.post(callbackURL,
            data=json.dumps(returnParams)) as r:
                responseStr = await r.text()
                printx("[3b] Callback endpoint returned:")

def printx(strtoPrint):
    print(strtoPrint)
    # pass

def dummy():
    pass

if __name__ == '__main__':
    if len(sys.argv) > 1:
        print("Setting serverURLPath")
        serverURLPath = sys.argv[1]
    try:
        print("Run webserver - workers=1")
        app.run(host="0.0.0.0", port=80, workers=1)
    except:
        print("Run webserver")
        app.run(host="0.0.0.0", port=80)