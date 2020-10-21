import sys
import os
from datetime import datetime
from dateutil.tz import gettz
import discord

date_start = datetime.strptime(
    os.environ["DATE_START"] + " 06+0900", "%Y-%m-%d %H%z")  # 初日5時は不要
date_end = datetime.strptime(
    os.environ["DATE_END"] + " 23:59:59+0900", "%Y-%m-%d %H:%M:%S%z")
now = datetime.now(gettz("Asia/Tokyo"))

if now <= date_start or date_end < now:
    print("Outside the clan battle period")
    sys.exit()

client = discord.Client()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    guild = discord.utils.get(client.guilds, name="検証用")
    remain = discord.utils.get(guild.channels, name="残凸把握板")
    announce = discord.utils.get(guild.channels, name="残凸時報")

    if now.day == date_end.day and 5 <= now.hour:
        left_hour = 24 - now.hour
    elif 0 <= now.hour < 5:
        left_hour = 5 - now.hour
    else:
        left_hour = 24 + 5 - now.hour

    send_message = now.strftime('%Y-%m-%d %H時') + "の凸状況\n"
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

                left_all = left3 * 3 + left2 * 2 + left1
                send_message += "あと" + \
                    str(left_hour) + "時間で" + str(left_all) + "凸\n"
                send_message += "一時間あたり" + \
                    str(round(left_all / left_hour, 2)) + "凸必要です"

                await announce.send(send_message)
                break

    await client.close()

token = os.environ["DISCORD_TOKEN"]
client.run(token)
