projects =
    <b>📁 My Projects</b>

projects-button-create = ➕ Add project
projects-button-settings = ⚙️ General Settings

project =
    <i>Project</i>: <b>{ $name }</b>

# Настройки сообщений
project-button-post_settings = 📨 Post Settings
project-post_settings =
    <b>📨 Message Settings</b>

    <i>In this section, you can configure the configuration of received messages</i>

project-button-posting_all = 📮 Forwarding: All posts
project-button-posting_keywords = 📮 Forwarding: By keywords
project-button-name = 📋 Rename project
project-button-connect = 🌐 Connect groups
project-button-delete = 🗑 Delete project
project-delete-confirm = 🚫 Press again to confirm
project-deleted = ✅ Project deleted

project-status-enabled = ✅ Enabled
project-status-disabled = ❌ Disabled
project-status-button-disable = 🟢 Disable project
project-status-disabled = 🆗 Project disabled
project-status-button-enable = 🔴 Enable project
project-status-enabled = 🆗 Project enabled
project-status-settings-button-disable = 🟢 Disable settings
project-status-settings-disabled = 🆗 Settings disabled
project-status-settings-button-enable = 🔴 Enable settings
project-status-settings-enabled = 🆗 Settings enabled

# Настройки отложенных постов
project-button-deferred_messages = ⌛Deferred messages
project-deferred_messages =
    <b>⌛Deferred messages</b>

    <i>This function publishes messages with a delay according to the selected time.

    If the time is not selected, the posts are published immediately in the feed.</i>

    👇 Choose the time of publication of deferred posts
project-deferred_messages-button-min_5 = 5 min
project-deferred_messages-button-min_30 = 30 min
project-deferred_messages-button-hours_1 = 1 hour
project-deferred_messages-button-hours_3 = 3 hour
project-deferred_messages-button-hours_6 = 6 hours
project-deferred_messages-button-hours_24 = 24 hours
project-deferred_messages-button-enabled = 🟢
project-deferred_messages-button-disabled = 🔴

project-button-duplicates = ✂️ Deleting messages
project-duplicates =
    <b>✂️ Deleting repeated messages</b>

    <i>This option allows you to receive only the first message from the sender, while subsequent ones will be blocked for an hour. This helps to clean up the chat from unwanted spam.</i>

    👇 Choose the options for which repeated of messages will be deleted
project-duplicates-button-enabled = 🟢
project-duplicates-button-disabled = 🔴
project-duplicates-button-text = Text-based
project-duplicates-button-user_id = User-based

project-button-signatures = 🖍 Adding a signature
project-button-delete_signature = Delete a signature
project-signatures =
    <b>🖍 Adding a signature</b>

    <i>This function allows you to add signatures to forwarded messages. You can enter values up to 100 characters.</i>

    <b>To delete a signature, click on it</b>

# Настройки замены текстов
project-button-replacing_text = 🔁 Replacing the text
project-replacing_text =
    <b>🔁 Replacing the text</b>

    <i>This function allows you to replace/delete words/phrases from forwarded messages. You can enter a value of up to 100 characters.</i>

    Example: The word "black" will be replaced with "white" or deleted depending on your setting.

    <b>To delete a key, click on it</b>
project-replacing_text_1 =
    <b>🔁 Text replacement</b>

    <b>Step [1/2] - Creating a key to replace or delete</b>

    👇Enter the word or phrase that you want to replace or remove from the text👇
project-replacing_text_2 =
    <b>🔁 Text replacement</b>

    <b>Step [2/2] - Creating a key to replace or delete</b>

    👇Enter a word or phrase that replaces the previous value.

    If you only want to delete from the text, click Skip

project-replacing_text-button-add_keyword = ➕Add a word
project-replacing_text-button-skip = Skip
project-replacing_text-warning_long = Please enter a word that does not exceed 100 characters in length
project-replacing_text-warning_dublicate = This keyword is already in use. Please select another one or delete the current one


project-response =
    <b>📝 Post parameters</b>

    <i>Enable and disable the parameters that will be displayed in the recipient group/channel</i>
project-response-button = 📝 Post parameters
project-response-button-include_username = Post author
project-response-button-include_project_name = Project name
project-response-button-include_media = Media files
project-response-button-include_text = Keyword
project-response-button-include_usernames = Usernames
project-response-button-include_hashtags = Hashtags
project-response-button-include_links_from_text = Links
project-response-button-include_emoji = Emoji
project-response-button-enabled = 🟢
project-response-button-disabled = 🔴


project-name =
    <b>📋 Rename project</b>

    👇 Enter the new project name

project-name-updated =
    ✅ Saved

project-connect =
    <b>🌐 Connect Groups and Channels</b>

    📌 To work with this bot, you need to add sender/receiver groups/channels data and grant the bot admin rights in the receiver group/channel.

    <i>If connection problems occur, read the instructions</i>

    Current data👇

    📤 <b>Sender:</b>
    <i>{ $sender }</i>
    --------------------
    📥 <b>Receiver:</b>
    <i>{ $receiver }</i>

project-connect-sender-absent = Absent
project-connect-button-instruction = 📄 Instructions
project-connect-button-sender = 📤 Sender
project-connect-button-receiver = 📥 Receiver
project-connect-button-chait = VALIDATION
project-connect-button-channel = + Channel
project-connect-button-channel_1 = + Group
project-connect-button-channel_2 = + Forum
project-connect-button-choose_forum = Choose forum
project-connect-instruction-instruction =
    <b>🌐 Connecting the Receiver</b>

    📌 When adding a receiver for the first time, click the corresponding button "+ Group", "+ Forum" or "+ Channel"

    If the required receiver is already present in other projects, then select it from the list below

project-connect-receiver_forum =
    <b>🌐 Connecting the receiver: Forum</b>

    Manual:

    1. Select a forum group from the list
    2. Grant the bot administrator rights
    3. Specify the link to the minichat in which the bot will work.

project-connect-receiver-not_owner = 🚫 You are not the owner of the receiver group
project-connect-receiver-not_found = 🚫 Receiver group not found
project-connect-receiver-minichat_not_found =
    Invalid minichat link/id format
    The receiver group is not connected!
project-connect-receiver-success = ✅ Receiver group added to the { $name } project
project-connect-receiver-already_set = 🆗 This receiver group is already added to the { $name } project
project-connect-receiver-input_id = 👇Send a link to the minichat
project-connect-receiver-minichat_success =
    ✅ Minichat successfully added to the receiver group

project-connect-sender-minichat_success =
    Minichat is connected to the sending chat
project-connect-sender =
    <b>🔌 Group Connection</b>

    Enter <b>@username, link or invitation link</b> from where the data will be sent

project-connect-sender-success = ✅ Sender group added to the { $name } project
project-connect-sender-already_set = 🆗 This sender group is already added to the { $name } project
project-connect-sender-error = 🚫 Error adding sender group
project-connect-sender-no_accounts = 🚫 No available accounts, contact the administrator
project-connect-sender-not_found = 🚫 Sender group not found
project-connect-sender-can_not_get_chat = 🚫 Failed to get information about the sender group. If you are sure the group link is correct, contact the administrator
project-connect-sender-processing = 🔄 Adding sender group...
project-not_found = 🚫 Project not found

project-keyword-type-contains = 🔍 Contains phrase
project-keyword-type-exact = ❗ Exact match
project-keyword-type-signature = 🖍 Signature

project-button-keywords = 🔑 Keywords
project-button-stop_keywords = 🚫 Stop Words
project-button-allowed_senders = ✅ Senders
project-button-stop_senders = ❌ Banned senders

project-button-keyword = 🔑 Keyword
project-button-stop_keyword = 🚫 Stop Word
project-button-allowed_sender = ✅ Sender
project-button-stop_sender = ❌ Sender

project-button-keywords-possessive = 🔑 Keywords
project-button-stop_keywords-possessive = 🚫 Stop Words
project-button-allowed_senders-possessive = ✅ Allowed Senders
project-button-stop_senders-possessive =
    ❌ <b>Banned Senders</b>

    <i>Add the username or name of the sender from whom you do not want to receive messages. Messages from these senders will not be forwarded.</i>
project-button-keyword-possessive = 🔑 Keyword
project-button-stop_keyword-possessive = 🚫 Stop Word
project-button-allowed_sender-possessive = ✅ Sender
project-button-stop_sender-possessive = ❌ Sender

# Добавить ключевое слово
project-button-add-keyword =
    ➕{ $sign } Add{ $keyword_type }

project-keywords =
    <b>{ $sign } { $keyword_type }</b>

    { $formats }
    <b>To delete a word - click on it</b>

project-keywords-formats =
    Words are processed in the format:

    <i>{ $types }
    </i>

project-keyword-create =
    <b>Create { $keyword_type }</b>

project-keyword-create-type =
    <b>Create { $keyword_type }</b>

    Example of match types:

    <i>🔍"World" - will match "World", "Peaceful World"
    ❗"World" - will match only "World"</i>

    Select the required type👇

project-keyword-create-word =
    <b>Create { $keyword_type }</b>

    Enter text 👇

project-keyword-create-warning =
    ⚠️ Attention! Such a keyword already exists in the project

project-keyword-create-success =
    ✅ { $keyword_type } "{ $keyword }" added to the { $project_name } project

project-keyword-not_found = 🚫 { $keyword_type } not found

project-keyword-delete-confirm = 🚫 Press again to confirm
project-keyword-deleted = ✅ { $keyword_type } deleted
project-keyword-delete-signature =
    <b>🖍 Project signature:</b>

    { $signature }
