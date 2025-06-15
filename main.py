import discord
from discord.ext import commands
import os
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

class SprintBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        @self.tree.command(name="sprintstart", description="Start a writing sprint")
        async def sprintstart(interaction: discord.Interaction):
            await interaction.response.send_message("✅ Bot is alive and received your sprint command.")

    async def on_ready(self):
        print(f"Bot is ready as {self.user}")
        try:
            synced = await self.tree.sync()
            print(f"Synced {len(synced)} commands.")
        except Exception as e:
            print(f"Error syncing commands: {e}")

async def main():
    async with SprintBot() as bot:
        await bot.start(TOKEN)

asyncio.run(main())
