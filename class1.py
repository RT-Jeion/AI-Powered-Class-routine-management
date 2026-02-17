import pandas as pd
import ast
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

# Final shift_dt


# from subjects.csv
sub_dt = pd.read_csv("subjects.csv")
sub_dt = sub_dt[["id", "name", "code", "department"]]
# Final sub_dt


# from subject_groups.csv
sub_grp_dt = pd.read_csv("subject_groups.csv")
sub_grp_dt = sub_grp_dt[["id", "name", "grp_code", "has_subjects"]]
sub_grp_dt = sub_grp_dt.rename(columns={"id":"grp_id"})
sub_grp_dt["has_subjects"] = sub_grp_dt["has_subjects"].apply(ast.literal_eval)
# Final sub_grp_dt


# From teachers.csv
teacher_dt = pd.read_csv("teachers.csv")
teacher_dt = teacher_dt[["id","name","code", "department", "designation"]]

# Final teacher_dt

if __name__ == "__main__":
    print("Class Data: ")
    print(class_dt)

    print("\nSection Data: ")
    print(section_dt)

    print("\nClass Room Data: ")
    print(class_room_dt)

    print("\nShift Data: ")
    print(shift_dt)

    print("\nSubject Data: ")
    print(sub_dt)

    print("\nGroup Subject Data: ")
    print(sub_grp_dt)

    print("\nTeacher Data: ")
    print(teacher_dt)
