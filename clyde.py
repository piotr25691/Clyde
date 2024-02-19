import os
import asyncio

import discord
import httpx
from dotenv import load_dotenv

# prevent leaking any tokens to cause bans or blocks
load_dotenv()

owner = 603635602809946113


class Clyde(discord.Client):
    async def on_connect(self):
        print("Clyde has connected to Discord.")

    async def on_ready(self):
        print("Clyde ready!")

    async def on_message(self, message):
        # specify user ids forbidden from using clyde, eg. 691187099570929684
        forbidden = []

        if message.author.id in forbidden:
            print("Ignoring message")
            return

        if message.author == self.user:
            print("Ignoring self message")
            return

        if message.author.bot:
            print("Ignoring bot message")
            return

        if (
            self.user.mentioned_in(message)
            or not message.guild
            or message.channel.type == discord.ChannelType.public_thread
        ):
            ms = await message.reply("\u200b:clock3:", mention_author=False)
            async with message.channel.typing():
                prompt = message.content.replace(self.user.mention, "\u200b").strip()

                async with httpx.AsyncClient(timeout=None) as web:
                    try:
                        # run ai externally via an attached api
                        response = await web.post(
                            "http://127.0.0.1:8001/gpt",
                            json={"prompt": prompt, "type": "g4f"},
                        )
                    except httpx.ConnectError:
                        # server offline error response
                        await ms.edit("\u200b:earth_africa::x:")
                        user = self.get_user(owner)
                        await user.send(
                            "# Oh shit!\nError 2 has occurred: The API server is offline.\n\n"
                            "Please restart the API server before trying to use ChatGPT."
                        )
                        await asyncio.sleep(30)
                        return await ms.delete()

                    if response.status_code == 200:
                        # correct response
                        gpt_message = response.json()["message"]
                        if len(gpt_message) <= 2000:
                            return await ms.edit(gpt_message)
                        # too large response
                        await ms.edit("\u200b:scroll::warning:")
                        await asyncio.sleep(30)
                        return await ms.delete()

                    # error response
                    user = self.get_user(owner)
                    newline = "\n"
                    await ms.edit("\u200b:scroll::x:")
                    await user.send(
                        f"# Oh shit!\n"
                        f"Error {response.json()['code']} has occurred: {response.json()['error']}\n"
                        f"The following errors were caught:\n{newline.join(response.json()['errors'])}\n\n"
                        f"If someone else got this error, tell them to retry their request."
                    )  # only the owner id will get this
                    await asyncio.sleep(30)
                    return await ms.delete()


client = Clyde(max_messages=None, chunk_guilds_at_startup=False)
client.run(os.getenv("TOKEN"))
