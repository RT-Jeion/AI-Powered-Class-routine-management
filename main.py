import pandas as pd
from class1 import class_dt, section_dt, class_room_dt, shift_dt, sub_dt, sub_grp_dt, teacher_dt 

sec_sub_dt = pd.merge(section_dt, sub_grp_dt, on="grp_code", how="left")

sec_sub_dt.drop(["name_x", "name_y"], axis=1, inplace= True)


def time_convert(t):
    t = t.split(":")
    return float(t[0]) + ( float(t[1]) + (float(t[2]) / 60))/60

def time_duration(row):
    time1 = row["start"]
    time2 = row["end"]
    return time_convert(time2) - time_convert(time1)


shift_dt["duration"] = shift_dt[["start", "end"]].apply(time_duration, axis=1)





if __name__ == "__main__":
    print("Classes:")
    print(class_dt)

    print("\nSections:")
    print(section_dt)
    
    print("\nClass Rooms:")
    print(class_room_dt)
    
    print("\nShifts:")
    print(shift_dt)
    
    print("\nSubjects:")
    print(sub_dt)
    
    print("\nGroup Subjects:")
    print(sub_grp_dt)
    
    print("\nTeachers:")
    print(teacher_dt)
    
    print("\nSection with Subjects mapping:")
    print(sec_sub_dt)
    
