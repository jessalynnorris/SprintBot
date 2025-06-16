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

@tree.command(name="sprintstart", description="Start a writing sprint")
async def sprintstart(interaction: discord.Interaction):
    await interaction.response.send_message(
        "✅ Bot is alive and received your sprint command.\nClick below to join the sprint.",
        view=StartView(bot)
    )

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

class StartView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Join Sprint", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(StartingWordModal(self.bot, interaction.user))

class StartingWordModal(discord.ui.Modal, title="Enter Starting Word Count"):
    def __init__(self, bot, user):
        super().__init__()
        self.bot = bot
        self.user = user

        self.word_count = discord.ui.TextInput(
            label="Starting word count",
            placeholder="e.g., 12000",
            required=True
        )
        self.add_item(self.word_count)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            count = int(self.word_count.value.replace(",", ""))
        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ephemeral=True)
            return

        self.bot.sprint_data[self.user.id] = {
            "user": self.user,
            "start": count
        }

        await interaction.response.send_message(
            f"Starting at {count} words, {self.user.mention} joins the sprint. Let’s hope they understand priorities.",
            ephemeral=False
        )
