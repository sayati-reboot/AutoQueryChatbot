from chat_manager import process_manager
print('SQL agent to query the customer DB')
print('Type quit and then press enter to exit the chat')

while True:
    q=input('What do you want to query?')
    if q.lower() == 'quit':
        break
    response = process_manager(q)
    print(response)
