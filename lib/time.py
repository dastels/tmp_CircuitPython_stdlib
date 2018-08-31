# MIT License
# Copyright 2018 Noralf Trønnes

from _time import localtime, mktime, monotonic, sleep, struct_time, time



def checktm(t):
    try:
        t.tm_year
    except AttributeError:
        if len(t) != 9:
            raise TypeError('function takes exactly 9 arguments ({} given)'.format(len(t)))
        t = struct_time(t)

#    if t.tm_year < 0:
#         raise ValueError("year out of range")

    if t.tm_mon == 0:
        tmp = list(t)
        tmp[1] = 1
        t = struct_time(tuple(tmp))
    if t.tm_mon < 1 or t.tm_mon > 12:
         raise ValueError("month out of range")

    if t.tm_mday == 0:
        tmp = list(t)
        tmp[2] = 1
        t = struct_time(tuple(tmp))
    if t.tm_mday < 1 or t.tm_mday > 31:
        raise ValueError("day of month out of range")

    if t.tm_hour < 0 or t.tm_hour > 23:
        raise ValueError("hour out of range")

    if t.tm_min < 0 or t.tm_min > 59:
        raise ValueError("minute out of range")

    if t.tm_sec < 0 or t.tm_sec > 61:
        raise ValueError("seconds out of range")

    if t.tm_wday < 0 or t.tm_wday > 6:
        raise ValueError("day of week out of range")

    if t.tm_yday == 0:
        tmp = list(t)
        tmp[7] = 1
        t = struct_time(tuple(tmp))
    if t.tm_yday < 1 or t.tm_yday > 366:
        raise ValueError("day of year out of range")

    return t



altzone = 0

def asctime(t=None):
    if t is None:
        t = localtime()
    else:
        t = checktm(t)
    # 'Sun Jun 20 23:21:05 1993'
    return strftime('%a %b %_d %H:%M:%S %Y', t)

#clock()
#clock_getres(clk_id)
#clock_gettime(clk_id)
#clock_settime(clk_id, time)
#CLOCK_HIGHRES
#CLOCK_MONOTONIC
#CLOCK_MONOTONIC_RAW
#CLOCK_PROCESS_CPUTIME_ID
#CLOCK_REALTIME
#CLOCK_THREAD_CPUTIME_ID

def ctime(secs=None):
    return asctime(localtime(secs))

daylight = 0

#get_clock_info(name)

def gmtime(secs=None):
    if secs is None:
        secs = time()
    return localtime(secs)

#localtime([secs])
#mktime(t)
#monotonic()
#perf_counter()
#process_time()
#sleep(secs)

wday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

def strftime(_format, t=None):
    if t is None:
        t = localtime()
    else:
        t = checktm(t)

    s = ''
    modifier = False
    pad_with_spaces = False

    for c in _format:
        if c == '%':
            if modifier:
                modifier = False
                s += '%'
            else:
                modifier = True

        elif modifier:
            if c == '_':
                pad_with_spaces = True
                continue
            modifier = False
            if c == 'a':
                s += wday_names[t.tm_wday][:3]
            elif c == 'A':
                s += wday_names[t.tm_wday]
            elif c == 'b':
                s += month_names[t.tm_mon - 1][:3]
            elif c == 'B':
                s += month_names[t.tm_mon - 1]
            elif c == 'c':
                s += strftime('%a %b %d %H:%M:%S %Y', t)
            elif c == 'd':
                s += '{:{pad}d}'.format(t.tm_mday, pad='2' if pad_with_spaces else '02')
            elif c == 'H':
                #s += '{:02d}'.format(t.tm_hour)
                s += '{:{pad}d}'.format(t.tm_hour, pad='2' if pad_with_spaces else '02')
            elif c == 'I':
                s += 'TODO'
            elif c == 'j':
                #s += '{:03d}'.format(t.tm_yday)
                s += '{:{pad}d}'.format(t.tm_yday, pad='3' if pad_with_spaces else '03')
            elif c == 'm':
                #s += '{:02d}'.format(t.tm_mon)
                s += '{:{pad}d}'.format(t.tm_mon, pad='2' if pad_with_spaces else '02')
            elif c == 'M':
                #s += '{:02d}'.format(t.tm_min)
                s += '{:{pad}d}'.format(t.tm_min, pad='2' if pad_with_spaces else '02')
            elif c == 'p':
                s += 'TODO'
            elif c == 'S':
                #s += '{:02d}'.format(t.tm_sec)
                s += '{:{pad}d}'.format(t.tm_sec, pad='2' if pad_with_spaces else '02')
            elif c == 'U':
                s += 'TODO'
            elif c == 'w':
                s += '{:d}'.format(t.tm_wday + 1)
            elif c == 'W':
                s += 'TODO'
            elif c == 'x':
                s += strftime('%m/%d/%y', t)
            elif c == 'X':
                s += strftime('%H:%M:%S', t)
            elif c == 'y':
                s += '{:d}'.format(t.tm_year % 100)
            elif c == 'Y':
                s += '{:d}'.format(t.tm_year)
            elif c == 'z':
                s += 'TODO'
            else:
                s += '%' + c
            pad_with_spaces = False

        else:
            s += c

    return s



#strptime(string[, format])

#class time.struct_time
#time()

timezone = 0

tzname = 'UTC', None

#tzset()
