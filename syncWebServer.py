import sys
import aiohttp
import asyncio
import json
import uuid
from vibora import Vibora, JsonResponse, Request, Response

app = Vibora()

# dictionary of asyncio.Event() key'ed by unique responseID
responseEvents = {}
responseDetails = {
    "ID121324242": "This is the response back"
}

def getUniqueResponseID():
    return str(uuid.uuid4())

serverURLPath = "http://127.0.0.1:8000"

@app.route('/', methods=['GET', 'POST'])
async def home(request : Request):
    printx("[1a] / called")
    responseID = getUniqueResponseID()
    responseEvents[responseID] = asyncio.Event()
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
    await responseEvents[responseID].wait()
    printx('[1e] received response ...')
    responseObj = responseDetails[responseID]
    del responseEvents[responseID]
    del responseDetails[responseID]
    return JsonResponse(responseObj)

@app.route('/response', methods=['POST'])
async def responseReceiver(request : Request):
    # Really strange but the next call to dummy (or a print statement) is needed here for this method to work consistently??
    dummy()
    # printx("[4] In /response")
    requestBody = await request.json()
    responseID = requestBody['callbackResponseID']
    # print("[4a] responding for {0}".format(responseID))
    responseEvents[responseID].set()
    responseDetails[responseID] = requestBody
    return JsonResponse({'msg': 'ok'})

@app.route('/dummyMPOEndpoint', methods=['POST'])
async def mpoTest(request : Request):
    printx("[2] dummyMPOEndpoint called")
    requestBody = await request.json()
    asyncio.create_task(mpoEndpointTask(requestBody))
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
    # print(strtoPrint)
    pass

def dummy():
    pass

if __name__ == '__main__':
    if len(sys.argv) > 1:
        print("Setting serverURLPath")
        serverURLPath = sys.argv[1]
    app.run(host="0.0.0.0", port=8000)