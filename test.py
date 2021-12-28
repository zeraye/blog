import time

date = time.mktime((2021, 12, 28, 0, 0, 0, 0, 0, 0))

print(time.strftime("%b %d, %Y", time.gmtime(date)))