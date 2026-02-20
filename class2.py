from main import teacher_dt, sec_sub_dt, sub_dt


def find_eligible(subject_ids):
    dept_list = sub_dt[sub_dt["id"].isin(subject_ids)]["department"].unique()
    eligible = teacher_dt[teacher_dt["department"].isin(dept_list)]
    return list(eligible[["code"]])


sec_teacher_dt = sec_sub_dt[["code", "grp_code"]].copy()
sec_teacher_dt["teachers"] = sec_sub_dt["has_subjects"].apply(find_eligible)


if __name__ == "__main__":
    print(sec_teacher_dt)

