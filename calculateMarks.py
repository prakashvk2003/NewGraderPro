# grade_list must be rated in [0,10]

def calculate_cgpa(grade_list, credits_list):
    """
    Calculate CGPA for a single question.

    :param grade_list: List of grade_list for each key-factor score.
    :param credit_list: List of total credits for each key-factors.
    :return: CGPA after single question.
    """
    total_credits = sum(credits_list)
    weighted_cgpas = sum(cgpa * credit for cgpa, credit in zip(grade_list, credits_list))

    cgpa = weighted_cgpas / total_credits
    return round(cgpa, 2)


def cgpa_to_percentage(cgpa):
    """
    Convert CGPA to percentage.

    :param cgpa: Cumulative Grade Point Average.
    :return: Percentage equivalent of CGPA.
    """
    percentage = round(cgpa*9.5, 2)
    return percentage


def calculate_marks_obtained(rating_list, credit_list, total_marks):
    total_credits = sum(credit_list)
    weighted_cgpas = sum(cgpa * credit for cgpa, credit in zip(rating_list, credit_list))

    cgpa = weighted_cgpas / total_credits

    percentage = cgpa * 9.5

    marks_obtained = (percentage / 100) * total_marks
    return round(marks_obtained, 0)




# Example Usage

# grades = [8, 10, 10]  # Grade points for each key-factor score
# credits = [4, 3, 2]  # Credits for each key-factors

# marks_obtained = calculate_marks_obtained(grades, credits, 100)
# print("Marks Obtained:", marks_obtained)