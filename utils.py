import re

USER_TAG_BODY_RE = re.compile(r'^[A-Za-z0-9_]{2,20}$')
MAX_MESSAGE_LENGTH = 280


def normalize_user_tag(raw_tag):
    raw_tag = (raw_tag or '').strip()
    if raw_tag.startswith('@'):
        raw_tag = raw_tag[1:]
    return raw_tag.lower()


def validate_user_tag_format(raw_tag):
    errors = []
    tag = normalize_user_tag(raw_tag)
    if not USER_TAG_BODY_RE.match(tag):
        errors.append(
            'Il tag utente deve avere il formato @tag (2-20 caratteri: lettere, numeri, underscore).'
        )
    return errors


def validate_registration(first_name, last_name, user_tag, password, password2):
    errors = []
    if not (first_name or '').strip():
        errors.append('Il nome è obbligatorio.')
    if not (last_name or '').strip():
        errors.append('Il cognome è obbligatorio.')

    errors.extend(validate_user_tag_format(user_tag))

    if len(password or '') < 6:
        errors.append('La password deve essere lunga almeno 6 caratteri.')
    if password != password2:
        errors.append('Le due password non coincidono.')
    return errors


def validate_message_body(body):
    errors = []
    body = (body or '').strip()
    if not body:
        errors.append('Il messaggio non può essere vuoto.')
    elif len(body) > MAX_MESSAGE_LENGTH:
        errors.append(f'Il messaggio non può superare {MAX_MESSAGE_LENGTH} caratteri.')
    return errors
