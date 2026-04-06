from ContentFilter import ContentFilter

filter = ContentFilter(UseNLP=True)


print(filter.is_message_clean("bitch"))
