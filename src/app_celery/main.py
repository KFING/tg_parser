from celery import Celery
from celery.schedules import crontab

app = Celery('main', broker='redis://localhost:6379/0', backend='redis://localhost:6379/1')
app.conf.beat_schedule = {}
app.conf.timezone = 'UTC'

app.autodiscover_tasks(['src.app_celery.tasks', 'src.app_celery.manager'])

app.conf.beat_schedule = {
    'run-manager-every-minute': {
        'task': 'src.app_celery.manager.manager_task',
        'schedule': crontab(minute='*/1'),
    },
}
