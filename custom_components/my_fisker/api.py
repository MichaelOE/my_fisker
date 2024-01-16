#import asyncio
import json
import logging

import aiohttp

#import requests
from .const import API_TIMEOUT, TOKEN_URL, WSS_URL

# import websockets

_LOGGER = logging.getLogger(__name__)

headers = {"User-Agent": "MOBILE 1.0.0.0"}

HasAUTH = False
HasVIN = False
vin = ""


class MyFiskerAPI:
    def __init__(self, username: str, password: str):
        _LOGGER.debug("MyFiskerAPI init")
        self._username = username
        self._password = password

        self._token = ""
        self._timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)

    async def GetAuthTokenAsync(self):
        params = {"username": self._username, "password": self._password}
        async with aiohttp.ClientSession() as session, session.post(
            TOKEN_URL, data=params
        ) as response:
            data = await response.json()

            # Check if a key exists
            if "accessToken" in data:
                retVal = data["accessToken"]
            else:
                retVal = data["message"]

            self._token = retVal
            return self._token

    async def tokenReturn(self):
        return self._token

    async def fetch_data(self):
        ret = self.flatten_json(
            self.ParseDigitalTwinResponse(
                await self.GetWebsocketResponse("digital_twin")
            )
        )
        return ret

    async def GetProfiles(self):
        return self.ParseProfilesResponse(await self.GetWebsocketResponse("profiles"))

    async def GetWebsocketResponse(self, responseToReturn: str):
        HasAUTH = False
        HasVIN = HasAUTH

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(WSS_URL, headers=headers) as ws:
                await ws.send_str(json.dumps(self.GenerateVerifyRequest()))
                while True:
                    response = await ws.receive_str()
                    handler = json.loads(response)["handler"]

                    if handler == responseToReturn:
                        try:
                            await ws.close()
                        except Exception as e:
                            _LOGGER.debug(
                                f"Error occurred while closing WebSocket: {e}"
                            )
                        self.ParseDigitalTwinResponse(response)
                        return response

                    if HasAUTH is not True:
                        if handler == "verify":
                            HasAUTH = (
                                json.loads(response)["data"]["authenticated"] is True
                            )
                            # Send a message
                            # _LOGGER.debug(f"Sending 'GenerateProfilesRequest'")
                            await ws.send_str(
                                json.dumps(self.GenerateProfilesRequest())
                            )

                    if HasAUTH is True and HasVIN is not True:
                        if handler == "profiles":
                            vin = self.ParseProfilesResponse(response)
                            # print (f"vin = {vin}")
                            if vin != "":
                                self.HasVIN = True
                                # Send a message
                                _LOGGER.debug(
                                    f"Auth & VIN ok - Sending 'DigitalTwinRequest' to vin={vin}"
                                )
                                await ws.send_str(
                                    json.dumps(self.DigitalTwinRequest(vin))
                                )

                    if HasAUTH is True and HasVIN is True:
                        # _LOGGER.debug(f"Received message: {message}")
                        if handler == responseToReturn:
                            self.ParseDigitalTwinResponse(response)
                            _LOGGER.error(response)
                            try:
                                await ws.close()
                            except Exception as e:
                                _LOGGER.error(
                                    f"Error occurred while closing WebSocket: {e}"
                                )

                            return response

    def flatten_json(self, jsonIn):
        out = {}

        def flatten(x, name=""):
            if type(x) is dict:
                for a in x:
                    flatten(x[a], name + a + "_")
            elif type(x) is list:
                i = 0
                for a in x:
                    flatten(a, name + str(i) + "_")
                    i += 1
            else:
                out[name[:-1]] = x

        flatten(jsonIn)
        return out

    def ParseDigitalTwinResponse(self, jsonMsg):
        # _LOGGER.debug('Start ParseDigitalTwinResponse()')
        # Parse the JSON response into a Python dictionary
        data = json.loads(jsonMsg)
        # print (data)
        if data["handler"] != "digital_twin":
            _LOGGER.debug("ParseDigitalTwinResponse: Wrong answer from websocket")
            _LOGGER.debug(data)
            return "Wrong answer from websocket"

        # Now you can access the items in the JSON response as you would with a Python dictionary
        digital_twin = data["data"]
        vin = digital_twin["vin"]
        _LOGGER.debug(vin)
        online = digital_twin["online"]
        _LOGGER.debug(online)
        updated = digital_twin["updated"]
        _LOGGER.debug(updated)
        vehicle_speed = digital_twin["vehicle_speed"]["speed"]
        _LOGGER.debug(vehicle_speed)
        ip = digital_twin["ip"]
        _LOGGER.debug(ip)

        battery = digital_twin["battery"]
        state_of_charge = battery["state_of_charge"]
        _LOGGER.debug(state_of_charge)
        avg_cell_temp = battery["avg_cell_temp"]
        _LOGGER.debug(avg_cell_temp)
        charge_type = battery["charge_type"]
        _LOGGER.debug(charge_type)
        max_miles = battery["max_miles"]
        _LOGGER.debug(max_miles)
        state_of_charge = battery["state_of_charge"]
        _LOGGER.debug(state_of_charge)
        total_mileage_odometer = battery["total_mileage_odometer"]
        _LOGGER.debug(total_mileage_odometer)

        # Use the jsonpath expression to find the value in the data
        _LOGGER.debug(digital_twin)  # Outputs: value1
        return digital_twin

    def GenerateVerifyRequest(self):
        # _LOGGER.debug('Start GenerateVerifyRequest()')
        data = {}
        messageData = {}

        # token = self.GetAuthToken(username, password)
        token = self._token

        data["token"] = token
        messageData["data"] = data
        messageData["handler"] = "verify"
        # print (messageData)
        return messageData

    def ParseVerifyResponse(self, jsonMsg):
        # Parse the JSON response into a Python dictionary
        data = json.loads(jsonMsg)

        if data["handler"] != "verify":
            return "Wrong answer from websocket"

        # Now you can access the items in the JSON response as you would with a Python dictionary
        item1 = data["data"]["authenticated"]

        if item1 != "true":
            return "Not authenticated"

        result = item1
        _LOGGER.debug(result)  # Outputs: value1
        return True

    def GenerateProfilesRequest(self):
        # _LOGGER.debug('Start GenerateProfilesRequest()')
        messageData = {}

        messageData["handler"] = "profiles"
        # print (messageData)
        return messageData

    def DigitalTwinRequest(self, vin):
        # _LOGGER.debug('Start DigitalTwinRequest()')
        data = {}
        messageData = {}
        data["vin"] = vin
        messageData["data"] = data
        messageData["handler"] = "digital_twin"
        return messageData

    def ParseProfilesResponse(self, jsonMsg):
        # _LOGGER.debug('Start ParseProfilesResponse()')
        # Parse the JSON response into a Python dictionary
        data = json.loads(jsonMsg)
        # print (data)
        if data["handler"] != "profiles":
            _LOGGER.debug("ParseProfilesResponse: Wrong answer from websocket")
            _LOGGER.debug(data)
            return "Wrong answer from websocket"

        # Now you can access the items in the JSON response as you would with a Python dictionary
        item1 = data["data"][0]["vin"]

        # Use the jsonpath expression to find the value in the data
        result = item1
        return result


# class MyFiskerWSS:
#     def __init__(self, token: str):
#         _LOGGER.debug("MyFiskerWSS init")
#         self._token = token
#         self._timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)

# async def tokenReturn(self):
#     return self._token

# async def fetch_data(self):
#     ret = self.flatten_json(
#         self.ParseDigitalTwinResponse(await self.GetDigitalTwin())
#     )
#     return ret

# async def GetDigitalTwin(self):
#     HasAUTH = False
#     HasVIN = HasAUTH

#     async with aiohttp.ClientSession() as session:
#         async with session.ws_connect(WSS_URL, headers=headers) as ws:
#             await ws.send_str(json.dumps(self.GenerateVerifyRequest()))
#             while True:
#                 response = await ws.receive_str()
#                 handler = json.loads(response)["handler"]

#                 if handler == "digital_twin":
#                     try:
#                         await ws.close()
#                     except Exception as e:
#                         _LOGGER.debug(
#                             f"Error occurred while closing WebSocket: {e}"
#                         )
#                     self.ParseDigitalTwinResponse(response)
#                     return response

#                 if HasAUTH is not True:
#                     if handler == "verify":
#                         HasAUTH = (
#                             json.loads(response)["data"]["authenticated"] is True
#                         )
#                         # Send a message
#                         # _LOGGER.debug(f"Sending 'GenerateProfilesRequest'")
#                         await ws.send_str(
#                             json.dumps(self.GenerateProfilesRequest())
#                         )

#                 if HasAUTH is True and HasVIN is not True:
#                     if handler == "profiles":
#                         vin = self.ParseProfilesResponse(response)
#                         # print (f"vin = {vin}")
#                         if vin != "":
#                             self.HasVIN = True
#                             # Send a message
#                             _LOGGER.debug(
#                                 f"Auth & VIN ok - Sending 'DigitalTwinRequest' to vin={vin}"
#                             )
#                             await ws.send_str(
#                                 json.dumps(self.DigitalTwinRequest(vin))
#                             )

#                 if HasAUTH is True and HasVIN is True:
#                     # _LOGGER.debug(f"Received message: {message}")
#                     if handler == "digital_twin":
#                         self.ParseDigitalTwinResponse(response)
#                         _LOGGER.error(response)
#                         try:
#                             await ws.close()
#                         except Exception as e:
#                             _LOGGER.error(
#                                 f"Error occurred while closing WebSocket: {e}"
#                             )

#                         return response

# def flatten_json(self, jsonIn):
#     out = {}

#     def flatten(x, name=""):
#         if type(x) is dict:
#             for a in x:
#                 flatten(x[a], name + a + "_")
#         elif type(x) is list:
#             i = 0
#             for a in x:
#                 flatten(a, name + str(i) + "_")
#                 i += 1
#         else:
#             out[name[:-1]] = x

#     flatten(jsonIn)
#     return out

# def ParseDigitalTwinResponse(self, jsonMsg):
#     # _LOGGER.debug('Start ParseDigitalTwinResponse()')
#     # Parse the JSON response into a Python dictionary
#     data = json.loads(jsonMsg)
#     # print (data)
#     if data["handler"] != "digital_twin":
#         _LOGGER.debug("ParseDigitalTwinResponse: Wrong answer from websocket")
#         _LOGGER.debug(data)
#         return "Wrong answer from websocket"

#     # Now you can access the items in the JSON response as you would with a Python dictionary
#     digital_twin = data["data"]
#     vin = digital_twin["vin"]
#     _LOGGER.debug(vin)
#     online = digital_twin["online"]
#     _LOGGER.debug(online)
#     updated = digital_twin["updated"]
#     _LOGGER.debug(updated)
#     vehicle_speed = digital_twin["vehicle_speed"]["speed"]
#     _LOGGER.debug(vehicle_speed)
#     ip = digital_twin["ip"]
#     _LOGGER.debug(ip)

#     battery = digital_twin["battery"]
#     state_of_charge = battery["state_of_charge"]
#     _LOGGER.debug(state_of_charge)
#     avg_cell_temp = battery["avg_cell_temp"]
#     _LOGGER.debug(avg_cell_temp)
#     charge_type = battery["charge_type"]
#     _LOGGER.debug(charge_type)
#     max_miles = battery["max_miles"]
#     _LOGGER.debug(max_miles)
#     state_of_charge = battery["state_of_charge"]
#     _LOGGER.debug(state_of_charge)
#     total_mileage_odometer = battery["total_mileage_odometer"]
#     _LOGGER.debug(total_mileage_odometer)

#     # Use the jsonpath expression to find the value in the data
#     _LOGGER.debug(digital_twin)  # Outputs: value1
#     return digital_twin

# def GenerateVerifyRequest(self):
#     # _LOGGER.debug('Start GenerateVerifyRequest()')
#     data = {}
#     messageData = {}

#     # token = self.GetAuthToken(username, password)
#     token = self._token

#     data["token"] = token
#     messageData["data"] = data
#     messageData["handler"] = "verify"
#     # print (messageData)
#     return messageData

# def ParseVerifyResponse(self, jsonMsg):
#     # Parse the JSON response into a Python dictionary
#     data = json.loads(jsonMsg)

#     if data["handler"] != "verify":
#         return "Wrong answer from websocket"

#     # Now you can access the items in the JSON response as you would with a Python dictionary
#     item1 = data["data"]["authenticated"]

#     if item1 != "true":
#         return "Not authenticated"

#     result = item1
#     _LOGGER.debug(result)  # Outputs: value1
#     return True

# def GenerateProfilesRequest(self):
#     # _LOGGER.debug('Start GenerateProfilesRequest()')
#     messageData = {}

#     messageData["handler"] = "profiles"
#     # print (messageData)
#     return messageData

# def DigitalTwinRequest(self, vin):
#     # _LOGGER.debug('Start DigitalTwinRequest()')
#     data = {}
#     messageData = {}
#     data["vin"] = vin
#     messageData["data"] = data
#     messageData["handler"] = "digital_twin"
#     return messageData

# def ParseProfilesResponse(self, jsonMsg):
#     # _LOGGER.debug('Start ParseProfilesResponse()')
#     # Parse the JSON response into a Python dictionary
#     data = json.loads(jsonMsg)
#     # print (data)
#     if data["handler"] != "profiles":
#         _LOGGER.debug("ParseProfilesResponse: Wrong answer from websocket")
#         _LOGGER.debug(data)
#         return "Wrong answer from websocket"

#     # Now you can access the items in the JSON response as you would with a Python dictionary
#     item1 = data["data"][0]["vin"]

#     # Use the jsonpath expression to find the value in the data
#     result = item1
#     return result


class MyFiskerApiError(Exception):
    """Base exception for all MyFisker API errors"""


class AuthenticationError(MyFiskerApiError):
    """Authenatication failed"""


class RequestError(MyFiskerApiError):
    """Failed to get the results from the API"""

    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code


class RequestConnectionError(MyFiskerApiError):
    """Failed to make the request to the API"""


class RequestTimeoutError(MyFiskerApiError):
    """Failed to get the results from the API"""


class RequestRetryError(MyFiskerApiError):
    """Retries too many times"""


class RequestDataError(MyFiskerApiError):
    """Data is not valid"""


# websocket.enableTrace(True)


# Start the connection
# asyncio.get_event_loop().run_until_complete(connect())
