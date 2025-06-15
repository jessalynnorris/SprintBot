import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import os
import random

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

class SprintBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.sprint_data = {}
        self.roasts = [
            "Did you forget we were sprinting? Honestly.",
            "You had one job. Submit your words. That’s it.",
            "Some of us take this seriously, you know.",
            "Next time, maybe try showing up *and* finishing.",
            "I suppose deadlines are more of a suggestion to you?",
            "Are we even surprised? No. No, we are not.",
            "The library is quieter than your keyboard was.",
            "Remarkable. Truly. A sprint ghost. Write that story next.",
            "If vanishing were a skill, you'd have won.",
            "Incredible. Your invisibility spell worked perfectly."
        ]

        @self.tree.command(name="sprintstart", description="Start a writing sprint")
        async def sprintstart(interaction: discord.Interaction):
            self.sprint_data.clear()

            class SprintLengthModal(discord.ui.Modal, title="Set Sprint Length"):
                def __init__(modal_self):
                    super().__init__()
                    modal_self.minutes = discord.ui.TextInput(
                        label="Sprint length (in minutes)",
                        placeholder="e.g., 15",
                        required=True
                    )
                    modal_self.add_item(modal_self.minutes)

                async def on_submit(modal_self, interaction2: discord.Interaction):
                    try:
                        sprint_minutes = int(modal_self.minutes.value)
                    except ValueError:
                        await interaction2.response.send_message("Please enter a valid number.", ephemeral=True)
                        return

                    await interaction2.response.send_message(
                        "🪶 Your quills should be poised before the timer starts ticking. Join now and submit your starting word count. You have exactly 3 minutes before we begin.",
                        ephemeral=False
                    )

                    view = StartView(self)
                    message = await interaction.followup.send(
                        "Click below to join and input your starting word count:", view=view
                    )

                    await asyncio.sleep(180)
                    view.disable_all()
                    await message.edit(view=view)

                    await interaction2.followup.send(
                        f"⏰ Sprint begins now. Impress me, if you think you can.\n({sprint_minutes} minutes on the clock.)"
                    )

                    for remaining in range(sprint_minutes * 60, 0, -60):
                        await asyncio.sleep(60)

                    await interaction2.followup.send("🛎️ Time’s up! Quills down — it’s time to see what you achieved.")

                    final_view = FinalCountView(self)
                    message2 = await interaction.followup.send(
                        "Click to log your final word count below:", view=final_view
                    )

                    await asyncio.sleep(90)
                    final_view.disable_all()
                    await message2.edit(view=final_view)

                    await self.send_results(interaction2)

        async def send_results(self, interaction):
            results = []
            non_submitters = []

            for user_id, data in self.sprint_data.items():
                if "final" in data:
                    results.append((data["user"], data["final"] - data["start"]))
                else:
                    non_submitters.append(data["user"])

            results.sort(key=lambda x: x[1], reverse=True)

            lines = [f"**{user.mention}**: {words} words" for user, words in results]
            for user in non_submitters:
                roast = random.choice(self.roasts)
                lines.append(f"**{user.mention}**: didn’t bother submitting. {roast}")

            board = "\n".join(lines)
            await interaction.followup.send(f"🏆 Final Rankings:\n{board}")

bot = SprintBot()

class StartView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Join Sprint", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(StartingWordModal(self.bot, interaction.user))

    def disable_all(self):
        for child in self.children:
            child.disabled = True

class FinalCountView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Submit Final Count", style=discord.ButtonStyle.primary)
    async def submit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FinalWordModal(self.bot, interaction.user))

    def disable_all(self):
        for child in self.children:
            child.disabled = True

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

class FinalWordModal(discord.ui.Modal, title="Enter Final Word Count"):
    def __init__(self, bot, user):
        super().__init__()
        self.bot = bot
        self.user = user

        self.word_count = discord.ui.TextInput(
            label="Final word count",
            placeholder="e.g., 12345",
            required=True
        )
        self.add_item(self.word_count)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            final = int(self.word_count.value.replace(",", ""))
        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ephemeral=True)
            return

        if self.user.id in self.bot.sprint_data:
            self.bot.sprint_data[self.user.id]["final"] = final
        else:
            self.bot.sprint_data[self.user.id] = {
                "user": self.user,
                "start": 0,
                "final": final
            }

        await interaction.response.send_message(
            f"{self.user.mention} has submitted a final count of {final:,}. The full board will be displayed in 90 seconds.",
            ephemeral=False
        )

@bot.event
async def on_ready():
    print(f'Bot connected as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")

class SprintLengthModal(discord.ui.Modal, title="Set Sprint Length"):
    def __init__(self):
        super().__init__()
        self.minutes = discord.ui.TextInput(
            label="Sprint length (in minutes)",
            placeholder="e.g., 15",
            required=True
        )
        self.add_item(self.minutes)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"You chose {self.minutes.value} minutes!", ephemeral=True
        )

bot.run(TOKEN)
