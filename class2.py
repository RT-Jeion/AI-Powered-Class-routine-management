from class1 import shift_dt

def time_convert(t):
    t = t.split(":")
    return float(t[0]) + ( float(t[1]) + (float(t[2]) / 60))/60

def time_duration(row):
    time1 = row["start"]
    time2 = row["end"]
    return time_convert(time2) - time_convert(time1)


shift_dt["duration"] = shift_dt[["start", "end"]].apply(time_duration, axis=1)

if __name__ == "__main__":
    print(shift_dt)
