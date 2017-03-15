from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=1)
def update_sbi():
    http = urllib3.PoolManager()
    r = http.request('GET', 'https://ubike.herokuapp.com/update/sbi/')
    if r.status == 200:
        print('Updated SBI successed.')

@sched.scheduled_job('interval', hour=24)
def update_station():
    http = urllib3.PoolManager()
    r = http.request('GET', 'https://ubike.herokuapp.com/update/station/')
    if r.status == 200:
        print('Updated Station successed.')

sched.start()   
