import discord
from discord.ext import commands, tasks
from deep_translator import GoogleTranslator
import langdetect
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException
import os
from dotenv import load_dotenv
import json
from keep_alive import keep_alive
keep_alive()
from keep_alive import keep_alive
# Load environment variables
load_dotenv()

def load_settings():
    """Load user settings from JSON file"""
    try:
        with open('translator_settings.json', 'r') as f:
            settings = json.load(f)
            return settings.get('user_languages', {}), settings.get('user_translation_toggle', {}), settings.get('excluded_channels', [])
    except FileNotFoundError:
        return {}, {}, []
    except json.JSONDecodeError:
        print("Error reading settings file. Using default settings.")
        return {}, {}, []

def save_settings(user_languages, user_translation_toggle, excluded_channels):
    """Save user settings to JSON file"""
    settings = {
        'user_languages': {str(k): v for k, v in user_languages.items()},
        'user_translation_toggle': {str(k): v for k, v in user_translation_toggle.items()},
        'excluded_channels': excluded_channels
    }
    try:
        with open('translator_settings.json', 'w') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"Error saving settings: {e}")

# First, expand SUPPORTED_LANGUAGES with more languages:
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'it': 'Italian',
    'pt': 'Portuguese',
    'nl': 'Dutch',
    'pl': 'Polish',
    'ru': 'Russian',
    'ja': 'Japanese',
    'ko': 'Korean',
    'zh': 'Chinese',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'tr': 'Turkish',
    'vi': 'Vietnamese',
    'th': 'Thai',
    'ro': 'Romanian',
    'fr': 'French',
    'sw': 'Swahili'
}

# Set up bot with intents
intents = discord.Intents.default()
intents.message_content = True  # Enable in Discord Developer Portal

bot = commands.Bot(command_prefix="!", intents=intents)
bot.remove_command('help')  # Remove default help command

# Load saved settings
user_languages, user_translation_toggle, excluded_channels = load_settings()
# Convert string keys back to integers for user_languages
user_languages = {int(k): v for k, v in user_languages.items()}
user_translation_toggle = {int(k): v for k, v in user_translation_toggle.items()}

@bot.command(name='help')
async def help_command(ctx):
    """Display help information about the bot"""
    embed = discord.Embed(
        title="🌐 Translation Bot Help",
        description="I can help translate messages in this server to your preferred language!",
        color=discord.Color.blue()
    )

    # Commands Section
    embed.add_field(
        name="📝 Available Commands",
        value=(
            "**!setlang [code]**\n"
            "→ Set your preferred language\n"
            "→ Example: `!setlang es` for Spanish\n\n"
            "**!toggletranslation**\n"
            "→ Turn translations on/off for yourself\n\n"
            "**!excludechannel**\n"
            "→ Exclude the current channel from translations\n\n"
            "**!includechannel**\n"
            "→ Include the current channel for translations (undoes exclude)\n\n"
            "**!help**\n"
            "→ Show this help message"
        ),
        inline=False
    )

    # How it Works Section
    embed.add_field(
        name="💡 How it Works",
        value=(
            "1. Set your language using `!setlang`\n"
            "2. The bot will automatically translate messages to your language\n"
            "3. Translations appear in threads under the original message\n"
            "4. Use `!toggletranslation` to turn translations on/off\n"
            "5. Use `!excludechannel` to prevent translations in the current channel"
        ),
        inline=False
    )

    # Language Codes Section
    lang_list = ""
    for code, name in SUPPORTED_LANGUAGES.items():
        lang_list += f"`{code}` - {name}\n"

    embed.add_field(
        name="🗣️ Supported Languages",
        value=lang_list,
        inline=False
    )

    # Footer with extra info
    embed.set_footer(
        text="Tip: Messages are automatically translated when they're in a different language than your setting!")

    await ctx.send(embed=embed)

@bot.command()
async def setlang(ctx, lang_code):
    """Allows users to set their preferred language"""
    try:
        # Check if the language code is supported
        if lang_code not in SUPPORTED_LANGUAGES:
            supported_codes = ", ".join([f"`{code}`" for code in SUPPORTED_LANGUAGES.keys()])
            await ctx.send(
                f"{ctx.author.mention}, invalid language code. Please use one of these codes:\n{supported_codes}"
            )
            return

        # Test if the language code is valid with Google Translator
        GoogleTranslator(source='auto', target=lang_code).translate('test')
        user_languages[ctx.author.id] = lang_code
        # Set translation to enabled by default when setting language
        user_translation_toggle[ctx.author.id] = True
        # Save settings
        save_settings(user_languages, user_translation_toggle, excluded_channels)
        await ctx.send(
            f"{ctx.author.mention}, your preferred language is now set to `{lang_code}` ({SUPPORTED_LANGUAGES[lang_code]})! Translations are enabled.")
    except ValueError as e:
        await ctx.send(
            f"{ctx.author.mention}, there was an error setting your language. Please try again later."
        )
        print(f"Error setting language: {e}")

@bot.command()
async def toggletranslation(ctx):
    """Toggles translation on/off for the user"""
    user_id = ctx.author.id
    if user_id not in user_languages:
        await ctx.send(f"{ctx.author.mention}, please set your language first using !setlang [language code]")
        return

    current = user_translation_toggle.get(user_id, True)
    user_translation_toggle[user_id] = not current
    # Save settings
    save_settings(user_languages, user_translation_toggle, excluded_channels)
    status = "disabled" if current else "enabled"
    await ctx.send(f"{ctx.author.mention}, translations are now {status} for you!")

@bot.command()
async def excludechannel(ctx):
    """Excludes the current channel from translations"""
    channel_id = ctx.channel.id
    if channel_id not in excluded_channels:
        excluded_channels.append(channel_id)
        # Save settings
        save_settings(user_languages, user_translation_toggle, excluded_channels)
        await ctx.send("This channel is now excluded from translations.")
    else:
        await ctx.send("This channel is already excluded from translations.")

@bot.command()
async def includechannel(ctx):
    """Includes the current channel for translations (undoes exclude)"""
    channel_id = ctx.channel.id
    if channel_id in excluded_channels:
        excluded_channels.remove(channel_id)
        # Save settings
        save_settings(user_languages, user_translation_toggle, excluded_channels)
        await ctx.send("This channel is no longer excluded from translations.")
    else:
        await ctx.send("This channel was not excluded from translations.")

# Add a minimum confidence threshold for language detection
from langdetect import detect_langs

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    await bot.process_commands(message)

    if message.content.startswith(bot.command_prefix):
        return

    try:
        # Skip empty messages or messages that are too short
        if not message.content or len(message.content.strip()) < 2:
            return

        print(f"Processing message: {message.content}")

        # Detect source language
        try:
            langdetect.DetectorFactory.seed = 0
            detected_langs = detect_langs(message.content)
            most_probable = detected_langs[0]
            source_lang = most_probable.lang
            confidence = most_probable.prob
            print(f"Detected language: {source_lang} (confidence: {confidence})")

            if confidence < 0.5 or source_lang not in SUPPORTED_LANGUAGES:
                source_lang = 'auto'

        except Exception as e:
            print(f"Language detection error: {e}")
            source_lang = 'auto'

        # Create a main thread for all translations
        try:
            main_thread = await message.create_thread(
                name="Translations",
                auto_archive_duration=10080
            )

            # Create the base embed
            main_embed = discord.Embed(color=discord.Color.blue())
            main_embed.add_field(
                name=f"Original ({SUPPORTED_LANGUAGES.get(source_lang, 'Auto-detected')})",
                value=message.content,
                inline=False
            )
            
            main_embed.set_author(
                name=message.author.display_name,
                icon_url=message.author.avatar.url if message.author.avatar else None
            )

            # Track which languages we've already translated to
            translated_languages = set()
            users_to_notify = set()

            # Process translations for each user
            for user_id, target_lang in user_languages.items():
                # Skip if translations are disabled for this user
                if not user_translation_toggle.get(user_id, True):
                    continue

                # Skip if we've already translated to this language
                if target_lang in translated_languages:
                    users_to_notify.add(user_id)
                    continue

                # Skip if source and target languages are the same (unless source is auto)
                if source_lang != 'auto' and source_lang == target_lang:
                    continue

                try:
                    # Perform translation
                    translator = GoogleTranslator(source='auto', target=target_lang)
                    translated_text = translator.translate(text=message.content)

                    # Skip if translation is same as original
                    if translated_text.lower().strip() == message.content.lower().strip():
                        continue

                    # Add translation to main embed
                    main_embed.add_field(
                        name=f"Translation ({SUPPORTED_LANGUAGES[target_lang]})",
                        value=translated_text,
                        inline=False
                    )

                    translated_languages.add(target_lang)
                    users_to_notify.add(user_id)

                except Exception as e:
                    print(f"Translation error for {target_lang}: {e}")
                    continue

            # Only send if we have translations
            if len(translated_languages) > 0:
                if source_lang != 'auto':
                    main_embed.set_footer(text=f"Detection confidence: {confidence:.2%}")

                await main_thread.send(embed=main_embed)

                # Add all users who should see the translations
                for user_id in users_to_notify:
                    member = message.guild.get_member(user_id)
                    if member:
                        try:
                            await main_thread.add_user(member)
                        except discord.errors.Forbidden:
                            print(f"Couldn't add user {member.name} to thread")
            else:
                # If no translations were needed, delete the thread
                await main_thread.delete()

        except discord.errors.HTTPException as e:
            print(f"Error handling translations: {e}")

    except Exception as e:
        print(f"General translation error: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('Bot is ready!')
    print('To get started, users should use !help to see available commands')

# Get the token from environment variable
TOKEN = os.getenv('DISCORD_TOKEN')
if not TOKEN:
    raise ValueError("No Discord token found in environment variables!")

bot.run(TOKEN)