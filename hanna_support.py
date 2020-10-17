import os
from datetime import datetime
import pytz
import discord

client = discord.Client()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    guild = discord.utils.get(client.guilds, name="検証用")

    remain = discord.utils.get(guild.channels, name="残凸把握板")
    announce = discord.utils.get(guild.channels, name="残凸時報")

    now = datetime.now(pytz.timezone('Asia/Tokyo'))
    time_limmit = 5
    left_hour = 23 - now.hour + time_limmit

    send_message = str(now) + "の凸状況\n"
    messages = await remain.history(limit=100).flatten()
    for message in messages:
        if message.author.name == "ハンナ":
            condition = message.content
            if condition.startswith("```md"):
                # "残り〜凸"と空行を引く
                left3 = condition[condition.find(
                    "# 残り3凸"):condition.find("# 残り2凸")].count("\n") - 2
                send_message += "3凸：" + str(left3) + "人\n"

                left2 = condition[condition.find(
                    "# 残り2凸"):condition.find("# 残り1凸")].count("\n") - 2
                send_message += "2凸：" + str(left2) + "人\n"

                left1 = condition[condition.find(
                    "# 残り1凸"):condition.find("# 残り0凸")].count("\n") - 2
                send_message += "1凸：" + str(left1) + "人\n"

                left_all = left3 + left2 + left1
                send_message += "あと" + \
                    str(left_hour) + "時間で" + str(left_all) + "凸\n"
                send_message += "一時間あたり" + str(left_all / left_hour) + "凸必要です"

                await announce.send(send_message)
                break

    await client.close()

token = os.environ["DISCORD_TOKEN"]
client.run(token)
