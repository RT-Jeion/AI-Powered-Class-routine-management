import pandas as pd

# from classes.csv
class_dt = pd.read_csv("classes.csv")
class_dt = class_dt[["id", "name", "code"]]

# final Data: class_dt.


#from scetions.csv
section_dt = pd.read_csv("sections.csv")
section_dt = section_dt[["id","classes_id" ,"name", "code", "grp_code"]]

# Final data section_dtc

# From classroom.csv
class_room_dt = pd.read_csv("class_rooms.csv")
class_room_dt = class_room_dt[["id", "room_no","number_of_row","number_of_column", "each_brench_capacity"]]
class_room_dt["total_capacity"] = class_room_dt["number_of_row"] * class_room_dt["number_of_column"] * class_room_dt["each_brench_capacity"]
class_room_dt = class_room_dt.sort_values("room_no")

# Final class_room_dt.


#from shifts_management_logs.csv
shift_dt = pd.read_csv("shift_management_logs.csv")
shift_dt = shift_dt[["id","weekends", "start", "end"]]

if __name__ == "__main__":

    print(class_dt)
    print(section_dt)
    print(class_room_dt)
    print(shift_dt)
