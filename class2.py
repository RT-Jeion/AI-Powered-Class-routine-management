from  main import teacher_dt, sec_sub_map

teacher_dt = teacher_dt.drop(columns="has_subjects")
sec_sub_map = sec_sub_map.drop(columns="sub_names")

def find_eligible(section_sub):
    eligible = teacher_dt[teacher_dt["subjects"]].apply(lambda t_subs: any(s in section_sub for s in t_subs))

    return list(teacher_dt.loc[eligible, 'name'])

sec_teacher_dt = sec_sub_map[["code", "group_code"]].copy()
sec_teacher_dt["teachers"] = sec_sub_map["has_subjects"].apply(find_eligible)

print(sec_teacher_dt)
if __name__ == "__main__":
    print(sec_sub_map)
    print(teacher_dt)