#------------------------  Post Codes  ---------------------#

import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from info import TARGET_CHANNELS, ADMINS, DIRECT_GEN_DB, HOW_TO_POST_SHORT
from utils import gen_link, get_size, short_link, clean_title, get_poster

# Store user states
user_states = {}

async def delete_previous_reply(chat_id):
    if chat_id in user_states and "last_reply" in user_states[chat_id]:
        try:
            await user_states[chat_id]["last_reply"].delete()
        except Exception as e:
            print(f"Failed to delete message: {e}")

@Client.on_message(filters.command("post") & filters.user(ADMINS))
async def post_command(client, message):
    try:
        await message.reply(
            "**Welcome to the Rare Movie Post Feature!** 🎬\n\n"
            "**👉🏻 Send the number of files you want to add. 👈🏻**\n"
            "**‼️ Note: Only numbers are allowed.**",
            disable_web_page_preview=True
        )
        user_states[message.chat.id] = {"state": "awaiting_num_files"}
    except Exception as e:
        await message.reply(f"Error occurred: {e}")

@Client.on_message(filters.private & (filters.text | filters.media) & ~filters.command("post"))
async def handle_private_message(client, message):
    try:
        chat_id = message.chat.id
        await delete_previous_reply(chat_id)

        if chat_id in user_states:
            current_state = user_states[chat_id]["state"]

            if current_state == "awaiting_num_files":
                try:
                    num_files = int(message.text.strip())
                    if num_files <= 0:
                        rply = await message.reply("⏩ Forward the file")
                        user_states[chat_id]["last_reply"] = rply
                        return

                    user_states[chat_id] = {
                        "state": "awaiting_files",
                        "num_files": num_files,
                        "files_received": 0,
                        "file_ids": [],
                        "file_sizes": [],
                        "stream_links": []
                    }
                    reply_message = await message.reply("⏩ Forward the No: 1 file")
                    user_states[chat_id]["last_reply"] = reply_message
                except ValueError:
                    await message.reply("Invalid input. Please enter a valid number.")

            elif current_state == "awaiting_files":
                if message.photo:
                    file_id = message.photo.file_id
                    size = get_size(message.photo.file_size)
                elif message.document:
                    file_id = message.document.file_id
                    size = get_size(message.document.file_size)
                else:
                    await message.reply("Unsupported file type.")
                    return

                forwarded_message = await message.copy(chat_id=DIRECT_GEN_DB)
                stream_link = await gen_link(forwarded_message)

                user_states[chat_id]["file_ids"].append(file_id)
                user_states[chat_id]["file_sizes"].append(size)
                user_states[chat_id]["stream_links"].append(stream_link)

                user_states[chat_id]["files_received"] += 1
                files_received = user_states[chat_id]["files_received"]
                num_files_left = user_states[chat_id]["num_files"] - files_received

                if num_files_left > 0:
                    reply_message = await message.reply(f"⏩ Forward the No: {files_received + 1} file")
                    user_states[chat_id]["last_reply"] = reply_message
                else:
                    reply_message = await message.reply("**Now send the name of the movie (or) title**\n\n**Ex: Lover 2024 Tamil WebDL**")
                    user_states[chat_id]["state"] = "awaiting_title"
                    user_states[chat_id]["last_reply"] = reply_message

            elif current_state == "awaiting_title":
                title = message.text.strip()
                cleaned_title = clean_title(re.sub(r"[(){}:;'!]", "", title))

                imdb_data = await get_poster(cleaned_title)
                poster = imdb_data.get('poster') if imdb_data else None

                file_info = []
                for i, file_id in enumerate(user_states[chat_id].get("file_ids", [])):
                    try:
                        long_url = f"https://t.me/{client.me.username}?start=file_{file_id}"
                        short_link_url = await short_link(long_url)
                        if isinstance(short_link_url, tuple):  
                            short_link_url = short_link_url[0]  # Fix tuple issue
                        file_size = user_states[chat_id]["file_sizes"][i]
                        file_info.append(f"》{file_size} : [Click Here]({short_link_url})")
                    except Exception as e:
                        print(f"Error processing file ID {file_id}: {e}")

                file_info_text = "\n\n".join(file_info) if file_info else "No files available."

                stream_links_info = []
                for i, stream_link in enumerate(user_states[chat_id]["stream_links"]):
                    try:
                        short_stream_link_url = await short_link(stream_link)
                        if isinstance(short_stream_link_url, tuple):  
                            short_stream_link_url = short_stream_link_url[0]  # Fix tuple issue
                        stream_links_info.append(f"》{user_states[chat_id]['file_sizes'][i]} : [Click Here]({short_stream_link_url})")
                    except Exception as e:
                        print(f"Error shortening stream link: {e}")

                stream_links_text = "\n\n".join(stream_links_info)

                summary_message = f"**🎬 {title} Tamil HDRip**\n\n" \
                                  f"**[ 360p☆480p☆Hevc☆720p☆1080p ]✌**\n\n" \
                                  f"**🔻 Direct Telegram Files:**\n\n" \
                                  f"{file_info_text}\n\n" \
                                  f"**✅ [How to Download]({HOW_TO_POST_SHORT})**\n\n" \
                                  f"**🔻 Stream/Fast Download:**\n\n" \
                                  f"{stream_links_text}\n\n" \
                                  f"**Movie Group: @Roxy_Request_24_7**\n\n" \
                                  f"**❤️ Share with Friends ❤️**"

                await send_channel_selection(message)

                user_states[chat_id].update({
                    "summary_message": summary_message,
                    "poster": poster,
                    "file_info_text": file_info_text,
                    "stream_links_text": stream_links_text
                })

    except Exception as e:
        print(f"Error: {e}")
        await message.reply(f"Error occurred: {e}")

async def send_channel_selection(message):
    try:
        buttons = [[InlineKeyboardButton(text=name, callback_data=f"post_{chat_id}")] for chat_id, name in TARGET_CHANNELS.items()]
        reply_markup = InlineKeyboardMarkup(buttons)

        await message.reply("Select a channel to post:", reply_markup=reply_markup)
        await message.delete()
    except Exception as e:
        print(f"Error in channel selection: {e}")

@Client.on_callback_query(filters.regex(r"post_(\S+)"))
async def post_to_channel(client, callback_query):
    try:
        chat_id = callback_query.message.chat.id
        channel_id = int(callback_query.data.split("_")[1])

        summary_message = user_states[chat_id]["summary_message"]
        poster = user_states[chat_id].get("poster")

        if poster:
            await client.send_photo(channel_id, photo=poster, caption=summary_message)
        else:
            await client.send_message(channel_id, summary_message)

        await callback_query.message.reply(f"✅ Movie has been posted to {TARGET_CHANNELS[channel_id]}!")
        await callback_query.message.delete()

        del user_states[chat_id]

    except Exception as e:
        print(f"Error posting to channel: {e}")
