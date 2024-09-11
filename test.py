import requests

AS_HOST = 'localhost'
AS_PORT = '2380'
AS_ORIGIN = 'http://localhost:2380'
AS_REALM = 'bank'
AS_CLIENT = 'bank-app'
AS_SECRET = 'rifb7zJJzE2RKStq74pEPMg29W5GkyIC'
AS_USER = 'bank-app-user'
AS_PASS = 'bankappuserpass'


def get_authorization():
    url = f'{AS_ORIGIN}/auth/realms/{AS_REALM}/protocol/openid-connect/token'

    # Define the data payload
    payload = {
        'username': AS_USER,
        'password': AS_PASS,
        'grant_type': 'password',
        # 'grant_type': 'client_credentials',
        'client_id': AS_CLIENT,
        'client_secret': AS_SECRET
    }

    # Define the headers
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Make the POST request
    response = requests.post(url, data=payload, headers=headers)

    # Handle the response
    if response.status_code == 200:
        token_data = response.json()
        return "{} {}".format(token_data.get('token_type'), token_data.get('access_token'))
    else:
        # print(response.json())
        raise Exception('Invalid token response')


if __name__ == '__main__':
    authorization = get_authorization()
    resp = requests.get('http://localhost:8000/anything/get', headers={
        'Host': 'adagio-angora.gateway.bank',
        'Accept': 'application/json',
        'Authorization': authorization,
    })
    # print(authorization)
    print(resp.status_code)
    print(resp.content)
