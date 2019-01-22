def send_sms():
    text = f"Your confirmation code is: {str(4411)}"
    message = {"number": "+351" + "916040655", "message": "Hello world", 'key': '976c17a55b063482cfe956364a8b10a143b427e50Eh5Zurvxtl1U5BxJRDrHY1iZ'}
    response = post("http://textbelt.com/text", data=message)
    print(loads(response.text))
    if not loads(response.text)['success']:
        # print(response.status_code)
        # print(response.json())
        raise Exception(gettext("texbelt_error_send_sms"))
        print(response)
    print(response.text)
    return response


def send_sms_2():
    text = f"Your confirmation code is: {str(4411)}"
    headers = {"Authorization": "Bearer 47c3ef9e1cfa4af289345255193c3349", "Content-Type": "application/json",
               'User-Agent': 'test'}
    message = {"to": ["+351916040655"], "from": "447537432321", "body": text}
    response = post("https://api.clxcommunications.com/xms/v1/1557159d47be4a1491b168a046948875/batches", json=message,
                    headers=headers)
    print(response.text)
    return response
