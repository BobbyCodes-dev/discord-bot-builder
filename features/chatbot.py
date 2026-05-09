FEATURE_ID = "chatbot"
FEATURE_NAME = "Chatbot"
CATEGORY = "Fun"
DESCRIPTION = "Simple keyword-based chatbot with configurable responses"
ENV_VARS = ["CHATBOT_CHANNELS"]
DEPENDENCIES = []

BLOCK_CODE = r'''
class ChatbotCog(commands.Cog):
    """Simple keyword-based chatbot."""

    RESPONSES = {
        "hello": ["Hi there!", "Hey!", "Hello!", "Yo!"],
        "hi": ["Hello!", "Hey!", "Hi!"],
        "how are you": ["Doing great, thanks!", "Pretty good!", "All systems operational!"],
        "good morning": ["Good morning! ☀️", "Morning! Hope you have a great day!"],
        "good night": ["Good night! 😴", "Sleep well!", "Nighty night!"],
        "bye": ["Bye!", "See you later!", "Take care!"],
        "thanks": ["You're welcome!", "No problem!", "Anytime!", "😊"],
        "thank you": ["You're welcome!", "Happy to help!", "No problem!"],
        "lol": ["😂", "haha", "lol indeed"],
        "bruh": ["bruh moment", "smh"],
        "rip": ["F", "RIP 💀", "oof"],
        "pog": ["POGGERS", "POG", "Let's go!"],
    }

    def __init__(self, bot):
        self.bot = bot
        channel_ids = os.getenv("CHATBOT_CHANNELS", "")
        self.channels = [int(c.strip()) for c in channel_ids.split(",") if c.strip().isdigit()]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        # Only respond in configured channels, or all if none configured
        if self.channels and message.channel.id not in self.channels:
            return

        text = message.content.lower().strip()
        for keyword, responses in self.RESPONSES.items():
            if keyword in text:
                await message.channel.send(random.choice(responses))
                return

async def setup(bot):
    await bot.add_cog(ChatbotCog(bot))
'''
