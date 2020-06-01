import tools 

async def main(message):
    if 'lange' in message.content.lower():
        rep = "LE LANGE !!!!!"
    elif message.content.lower() == "stop":     # Si on a quitté une commande. Laisser tel quel.
        return
    else:
        rep = "Désolé, je n'ai pas compris 🤷‍♂️"
        
    await message.channel.send(rep)
