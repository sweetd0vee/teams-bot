from botbuilder.core import CardFactory
from botbuilder.schema.teams import FileConsentCard, FileConsentCardResponse, FileInfoCard
from botbuilder.schema.teams.additional_properties import ContentType
from botbuilder.schema import (
    Activity,
    ActivityTypes,
    Attachment,
    ChannelAccount,
    ConversationAccount,
)
import base64
from datetime import datetime
import json
import os
from .send_file import send_rss


def create_attachment(meta):
    """
    The file was uploaded, so display a FileInfoCard so the user can view the file in Teams.
    """
    download_card = FileInfoCard(
        unique_id = meta['_etag'],
        file_type = meta['filetype']
    )
    as_attachment = Attachment(
        content = download_card.serialize(),
        content_type = ContentType.FILE_INFO_CARD,
        name = meta['_fileName'],
        content_url = meta['_fileUrl']
    )
    return as_attachment


def create_reply(activity: Activity, text=None, text_format=None) -> Activity:
    """
        Creates an Activity for the responce with the same params as current Activity.
        :return: botbuilder.schema.Attachment
    """
    return Activity(
        type = ActivityTypes.message,
        timestamp = datetime.utcnow(),
        from_property = ChannelAccount(
            id = activity.recipient.id,
            name = activity.recipient.name
        ),
        recipient = ChannelAccount(
            id = activity.from_property.id,
            name = activity.from_property.name
        ),
        reply_to_id = activity.id,
        service_url = activity.service_url,
        channel_id = activity.channel_id,
        conversation = ConversationAccount(
        is_group = activity.conversation.is_group,
        id = activity.conversation.id,
            name = activity.conversation.name,
        ),
        text = text or "",
        text_format = text_format or None,
        locale = activity.locale,
    )


def get_filepath_in_drive(filepath: str, user_login: str, is_mailing = 0):
    filename = filepath.split('/')[-1]
    if not is_mailing:
        filepath = f"{filename}"
    return filepath


def create_file_card_activity(activity: Activity, filepath: str, user_login: str, text=None, text_format=None) -> Activity:
    """
        Create reply activity to the bot with attached file.
        Send a FileConsentCard to get permission from the user to upload a file.
    """
    filepath_in_drive = get_filepath_in_drive(filepath, user_login)
    meta = send_rss(filepath, filepath_in_drive, [user_login])
    as_attachment = create_attachment(meta)
    reply_activity = create_reply(activity, text, text_format)
    reply_activity.attachments = [as_attachment]
    os.remove(filepath)
    return reply_activity


def create_adaptive_card_attachment(card_path) -> Attachment:
    """
    Load an adaptive card attachment from file
    :return: Attachment
    """
    card_path = os.path.join(os.getcwd(), card_path)
    with open(card_path, "rb") as in_file:
        card_data = json.load(in_file)
    return CardFactory.adaptive_card(card_data)