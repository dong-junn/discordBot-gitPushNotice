import discord
from discord.ext import commands
import asyncio
from datetime import datetime
import logging
from aiohttp import web
import json

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Discord 봇 설정
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

CHANNEL_ID = 알림을 보낼 채널 ID로 설정하면 됩니다
ROLE_ID = 알림을 보내면서 언급할 역할 ID를 입력하면 됩니다

WEBHOOK_SECRET = 웹훅 시크릿 키를 입력하면 됩니다

@bot.event
async def on_ready():
    logger.info(f'{bot.user} has connected to Discord!')
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("봇이 활성화 되었습니다.")

async def handle_webhook(request):
    if request.headers.get('X-GitHub-Event') != 'push':
        return web.Response(status=200)
    
    payload = await request.json()
    
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        logger.error(f"채널을 찾을 수 없습니다. ID: {CHANNEL_ID}")
        return web.Response(status=500)
    
    role = channel.guild.get_role(ROLE_ID)
    if not role:
        logger.warning(f"역할을 찾을 수 없습니다. ID: {ROLE_ID}")
        role_mention = "@everyone"
    else:
        role_mention = role.mention

    for commit in payload['commits']:
        embed = discord.Embed(
            title="깃에 변경사항이 감지되었습니다",
            color=discord.Color.blue()
        )
        embed.add_field(name="Commit 메시지", value=commit['message'], inline=False)
        embed.add_field(name="작성자", value=commit['author']['name'], inline=True)
        embed.add_field(name="Branch", value=payload['ref'].split('/')[-1], inline=True)
        
        # 멘션과 임베드를 하나의 메시지로 결합하여 보냄
        await channel.send(f"{role_mention}\n", embed=embed)
        logger.info(f"새 커밋 알림을 보냈습니다: {commit['id']}")
    
    return web.Response(status=200)

async def start_webhook():
    app = web.Application()
    app.router.add_post('/webhook', handle_webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 9000 )
    await site.start()
    logger.info("Webhook 서버가 시작되었습니다.")

async def run_bot():
    await bot.start('봇 토큰을 여기에 입력하면 됩니다')

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(start_webhook())
    loop.run_until_complete(run_bot())
