#poster make features developer - Ansh Vachhani

import re
import logging
from pyrogram.errors.exceptions.bad_request_400 import MessageTooLong
from database.ia_filterdb import unpack_new_file_id
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram import Client, filters
from pyrogram.types import Message
from utils import get_size, gen_link, clean_title, get_poster, temp, short_link
from info import HOW_TO_POST_SHORT, ADMINS, DIRECT_GEN_DB

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
        await message.reply("**Wᴇʟᴄᴏᴍᴇ Tᴏ Usᴇ Oᴜʀ Rᴀʀᴇ Mᴏᴠɪᴇ Pᴏsᴛ Fᴇᴀᴛᴜʀᴇ:) Cᴏᴅᴇ ʙʏ [Rᴏxʏ ʟɪɴᴋᴢᴢ](https://t.me/PKlinkzz_admin_bot) 👨‍💻**\n\n**👉🏻Sᴇɴᴅ ᴛʜᴇ ɴᴜᴍʙᴇʀ ᴏғ ғɪʟᴇs ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴀᴅᴅ👈🏻**\n\n**‼️ Nᴏᴛᴇ : Oɴʟʏ ɴᴜᴍʙᴇʀ**", disable_web_page_preview=True)
        user_states[message.chat.id] = {"state": "awaiting_num_files"}
    except Exception as e:
        await message.reply(f"Error occurred: {e}")



@Client.on_message(filters.private & (filters.text | filters.media) & ~filters.command("post"))
async def handle_message(client, message):
    try:
        chat_id = message.chat.id
        
        await delete_previous_reply(chat_id)
        
        if chat_id in user_states:
            current_state = user_states[chat_id]["state"]

            if current_state == "awaiting_num_files":
                try:
                    num_files = int(message.text.strip())

                    if num_files <= 0:
                        rply = await message.reply("⏩ ғᴏʀᴡᴀʀᴅ ᴛʜᴇ ғɪʟᴇ")
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

                    reply_message = await message.reply("**⏩ ғᴏʀᴡᴀʀᴅ ᴛʜᴇ ɴᴏ: 1 ғɪʟᴇ**")
                    user_states[chat_id]["last_reply"] = reply_message
                        
                except ValueError:
                    await message.reply("Invalid input. Please enter a valid number.")

            elif current_state == "awaiting_files":
                if message.media:
                    file_type = message.media
                    forwarded_message = await message.copy(chat_id=DIRECT_GEN_DB)
                    file_id = unpack_new_file_id(getattr(message, file_type.value).file_id)
                    log_msg = await message.copy(chat_id=DIRECT_GEN_DB)
                    stream_link = await gen_link(log_msg)
                    
                    size = get_size(getattr(message, file_type.value).file_size)
                    await message.delete()
                else:
                    forwarded_message = await message.forward(chat_id=DIRECT_GEN_DB)
                    file_id = forwarded_message.message_id

                user_states[chat_id]["file_ids"].append(file_id)
                user_states[chat_id]["file_sizes"].append(size)
                user_states[chat_id]["stream_links"].append(stream_link)

                user_states[chat_id]["files_received"] += 1
                files_received = user_states[chat_id]["files_received"]
                num_files_left = user_states[chat_id]["num_files"] - files_received

                if num_files_left > 0:
                    files_text = "ғɪʟᴇ" if files_received == 1 else "ғɪʟᴇs"
                    reply_message = await message.reply(f"**⏩ ғᴏʀᴡᴀʀᴅ ᴛʜᴇ ɴᴏ: {files_received + 1} {files_text}**")
                    user_states[chat_id]["last_reply"] = reply_message                     
                else:
                    reply_message = await message.reply("**ɴᴏᴡ sᴇɴᴅ ᴛʜᴇ ɴᴀᴍᴇ ᴏғ ᴛʜᴇ ᴍᴏᴠɪᴇ**\n\n**ᴇx : ʟᴏᴠᴇʀ 𝟸𝟶𝟸𝟺 ʜɪɴᴅɪ ᴡᴇʙᴅʟ**")                    
                    user_states[chat_id]["state"] = "awaiting_title"
                    user_states[chat_id]["last_reply"] = reply_message
                    
            elif current_state == "awaiting_title":
                title = message.text.strip()
                title_clean = re.sub(r"[()\[\]{}:;'!]", "", title)
                cleaned_title = clean_title(title_clean)

                imdb_data = await get_poster(cleaned_title)
                poster = imdb_data.get('poster') if imdb_data else None

                file_info = []
                for i, file_id in enumerate(user_states[chat_id]["file_ids"]):
                    long_url = f"https://t.me/{temp.U_NAME}?start=aNsH_{file_id[0]}"
                    short_link_url = await short_link(long_url)
                    file_info.append(f"》{user_states[chat_id]['file_sizes'][i]} : {short_link_url}")
                
                file_info_text = "\n\n".join(file_info)

                stream_links_info = []
                for i, stream_link in enumerate(user_states[chat_id]["stream_links"]):
                    long_stream_url = stream_link[0]
                    short_stream_link_url = await short_link(long_stream_url)
                    stream_links_info.append(f"》{user_states[chat_id]['file_sizes'][i]} : {short_stream_link_url}")
                
                stream_links_text = "\n\n".join(stream_links_info)                
                summary_message = f"**🎬{title} Tamil HDRip**\n\n**[ 𝟹𝟼𝟶ᴘ☆𝟺𝟾𝟶ᴘ☆Hᴇᴠᴄ☆𝟽𝟸𝟶ᴘ☆𝟷𝟶𝟾𝟶ᴘ ]✌**\n\n**𓆩🔻𓆪 Dɪʀᴇᴄᴛ Tᴇʟᴇɢʀᴀᴍ Fɪʟᴇs Oɴʟʏ👇**\n\n**{file_info_text}**\n\n**✅ Note : [Hᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ]({HOW_TO_POST_SHORT})👀**\n\n**𓆩🔻𓆪 Sᴛʀᴇᴀᴍ/Fᴀsᴛ ᴅᴏᴡɴʟᴏᴀᴅ 👇**\n\n**{stream_links_text}**\n\n**✅ Note : [Hᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ]({HOW_TO_POST_SHORT})👀**\n\n**Mᴏᴠɪᴇ Gʀᴏᴜᴘ 𝟸𝟺/𝟽 : @Roxy_Request_24_7**\n\n**❤️‍🔥ー𖤍 𓆩 sʜᴀʀᴇ ᴡɪᴛʜ ғʀɪᴇɴᴅs 𓆪 𖤍ー❤️‍🔥**"
                summary_messages = f"{title_clean}, {cleaned_title}"
                if poster:
                    await message.reply_photo(poster, caption=summary_message)
                else:
                    await message.reply(summary_messages)
                    
                await message.delete()
                del user_states[chat_id]

        else:
            return
    except Exception as e:
        await message.reply(f"Error occurred: {e}")
