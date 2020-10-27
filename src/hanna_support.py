import sys
import os
import re
import json
import click
from datetime import datetime
from dateutil.tz import gettz
import discord

client = discord.Client()
now = datetime.now(gettz("Asia/Tokyo"))


@click.command()
@click.option('--out', '-o', is_flag=True)
@click.option('--purge', '-p', is_flag=True)
def main(out, purge):
    if out:
        # pylint: disable=unused-variable
        @client.event
        async def on_ready():
            print('We have logged in as {0.user}'.format(client))
            guilds_info = {}
            for i, guild in enumerate(client.guilds):
                channels_info = {}
                for j, channel in enumerate(guild.text_channels):
                    channels_info["channel" + str(j)] = {
                        "name": channel.name, "id": channel.id, "category": channel.category.name}
                guilds_info["guild" + str(i)] = {"name": guild.name,
                                                 "id": guild.id, "channels": channels_info}
            await client.close()

            with open("./data/guilds.json", mode="w") as f:
                f.write(json.dumps(guilds_info, ensure_ascii=False, indent=4))
    elif purge:
        # pylint: disable=unused-variable
        @client.event
        async def on_ready():
            print('We have logged in as {0.user}'.format(client))
            guild = discord.utils.get(
                client.guilds, id=int(os.environ["GUILD_ID"]))
            announce = discord.utils.get(
                guild.channels, id=int(os.environ["ANNOUNCE_CH_ID"]))

            def is_me(m):
                return m.author == client.user

            deleted = await announce.purge(limit=None, check=is_me)
            print("Deleted {} message(s)".format(len(deleted)))
            await client.close()
    else:
        global date_start
        date_start = datetime.strptime(
            os.environ["DATE_START"] + " 06+0900", "%Y/%m/%d %H%z")  # 初日5時は不要
        global date_end
        date_end = datetime.strptime(
            os.environ["DATE_END"] + " 23:59:59+0900", "%Y/%m/%d %H:%M:%S%z")

        if now <= date_start or date_end < now:
            print("Outside the clan battle period")
            return

        # pylint: disable=unused-variable
        @client.event
        async def on_ready():
            print('We have logged in as {0.user}'.format(client))
            guild = discord.utils.get(
                client.guilds, id=int(os.environ["GUILD_ID"]))
            reserve = discord.utils.get(
                guild.channels, id=int(os.environ["RESERVE_CH_ID"]))
            remain = discord.utils.get(
                guild.channels, id=int(os.environ["REMAIN_CH_ID"]))
            announce = discord.utils.get(
                guild.channels, id=int(os.environ["ANNOUNCE_CH_ID"]))

            if now.day == date_end.day and 5 <= now.hour:
                left_hour = 24 - now.hour
            elif 0 <= now.hour < 5:
                left_hour = 5 - now.hour
            else:
                left_hour = 24 + 5 - now.hour

            send_message = now.strftime('%Y/%m/%d %H時') + "の残凸状況\n"
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
                        if left_all == 0:
                            print("全員3凸済みの為スキップ")
                            break

                        if now.hour != 5:  # 5時は全員残3凸&ハンナの更新が間に合わないので出力しない
                            send_message += "あと" + \
                                str(left_hour) + "時間で" + str(left_all) + "凸\n"
                            send_message += "1時間あたり" + \
                                str(round(left_all / left_hour, 2)) + "凸必要です"
                            await announce.send(send_message)

                        message = (await reserve.history(limit=1, oldest_first=True).flatten())[0]
                        text = re.sub(
                            r"^残HP.*\n", "", message.content.replace("**", ""), flags=re.MULTILINE)
                        group = re.findall(
                            r".\ufe0f\u20e3 (.*)\n.*: (.*)万", text, flags=re.MULTILINE)
                        for i in range(5):
                            if group[i][1] != "0":
                                await announce.send("@everyone " + group[i][0] + "が" + group[i][1] +
                                                    "万足りていません、凸できる方はお願いします。")
                                break

                        break

            await client.close()

    token = os.environ["DISCORD_TOKEN"]
    client.run(token)


if __name__ == '__main__':
    # pylint: disable=no-value-for-parameter
    main()
