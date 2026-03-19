from firebase_admin import messaging

def send_push_notification(token, title, body):
    if not token:
        return

    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
    )

    messaging.send(message)


def send_bulk_push_notification(tokens, title, body):
    chunk_size = 500

    for i in range(0, len(tokens), chunk_size):
        chunk = tokens[i:i+chunk_size]

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            tokens=chunk,
        )

        messaging.send_multicast(message)