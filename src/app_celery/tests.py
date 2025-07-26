from datetime import datetime, timezone

START_OF_EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)

END_OF_EPOCH = datetime(2100, 1, 1, tzinfo=timezone.utc)

if START_OF_EPOCH > END_OF_EPOCH:
    print('START_OF_EPOCH')
else:
    print('END_OF_EPOCH')
